#!/usr/bin/env python3
"""Subida de vídeo exclusivamente PRIVADO con comprobación de canal y OAuth.

No hay opción de subir público o programar vídeo. Fallará si faltan credenciales.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from metadatos_youtube import es_duplicado, normalizar_etiquetas

BASE = Path(__file__).resolve().parent
OUT = BASE/"salida"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly"]
HISTORIAL = BASE/"historial_publicados.json"


def credenciales():
    valor = os.getenv("YOUTUBE_OAUTH_JSON","").strip()
    if not valor:
        raise RuntimeError("Falta YOUTUBE_OAUTH_JSON en GitHub Secrets")
    try:
        datos=json.loads(valor)
    except json.JSONDecodeError as e:
        raise RuntimeError("YOUTUBE_OAUTH_JSON no contiene JSON válido") from e
    if not isinstance(datos,dict) or not datos.get("refresh_token"):
        raise RuntimeError("YOUTUBE_OAUTH_JSON necesita refresh_token")
    cred=Credentials.from_authorized_user_info(datos,scopes=SCOPES)
    if not cred.valid:
        if not cred.refresh_token:
            raise RuntimeError("Token sin posibilidad de refrescar")
        cred.refresh(Request())
    if not cred.valid:
        raise RuntimeError("No se pudieron renovar credenciales OAuth")
    return cred


def cliente():
    return build("youtube","v3",credentials=credenciales(),cache_discovery=False)


def verificar_identidad(youtube):
    configuracion=json.loads((BASE/"config.json").read_text(encoding="utf-8"))
    esperado=configuracion.get("youtube_channel_id","").strip()
    configurado=os.getenv("YOUTUBE_CHANNEL_ID","").strip()
    if not esperado:
        raise RuntimeError("Falta youtube_channel_id en config.json")
    if configurado and configurado!=esperado:
        raise RuntimeError("El ID configurado en el entorno no coincide con config.json")
    respuesta=youtube.channels().list(part="id,snippet",mine=True).execute()
    canales=respuesta.get("items",[])
    if len(canales)!=1:
        raise RuntimeError("OAuth no devolvió exactamente un canal")
    canal=canales[0]
    if canal["id"]!=esperado:
        raise RuntimeError("CANAL INCORRECTO: token de YouTube no corresponde a Píxel Feroz")
    print("Canal autorizado:",canal["snippet"].get("title"),canal["id"])


def comprobar_archivos(formato):
    plan=json.loads((OUT/"plan.json").read_text(encoding="utf-8"))
    if plan.get("formato")!=formato:
        raise ValueError("Formato no coincide con el plan")
    if plan.get("estado")!="BORRADOR_PENDIENTE_REVISION":
        raise ValueError("Plan inválido")
    if plan.get("publicacion_automatica") is not False:
        raise ValueError("Publicación automática debe estar desactivada")
    if plan.get("revision_pendiente") is not True:
        raise ValueError("Se requiere una revisión editorial")
    titulo=plan.get("titulo_propuesto","").strip()
    if not 5<=len(titulo)<=100:
        raise ValueError("Título inválido")
    desc=(OUT/"descripcion.txt").read_text(encoding="utf-8").strip()
    if not desc or "https://" not in desc:
        raise ValueError("Descripción sin fuentes")
    archivo=OUT/("pixel_feroz_short.mp4" if formato=="short" else "pixel_feroz_largo.mp4")
    if not archivo.is_file() or archivo.stat().st_size<20000:
        raise ValueError("Falta MP4 o está vacío")
    miniatura=OUT/"miniatura.jpg"
    if not miniatura.is_file():
        raise ValueError("Falta miniatura")
    if miniatura.stat().st_size>2*1024*1024:
        raise ValueError("Miniatura demasiado grande para YouTube")
    return plan,titulo,desc,archivo,miniatura



def rechazar_subida_duplicada(youtube, tema_id, formato='short'):
    """Busca vídeos previos del mismo tema en la lista de subidas de este canal.

    La búsqueda es deliberadamente conservadora: ante errores o demasiadas
    páginas, no permite una nueva carga que podría resultar duplicada.
    """
    respuesta = youtube.channels().list(
        part="contentDetails", mine=True
    ).execute()
    items = respuesta.get("items", [])
    if len(items) != 1:
        raise RuntimeError("No se pudo localizar el canal autorizado")
    uploads = (items[0].get("contentDetails", {})
               .get("relatedPlaylists", {}).get("uploads"))
    if not uploads:
        raise RuntimeError("No se pudo identificar la lista de subidas")

    pagina = None
    for numero in range(12):
        params = dict(part="contentDetails", playlistId=uploads, maxResults=50)
        if pagina:
            params["pageToken"] = pagina
        lote = youtube.playlistItems().list(**params).execute()
        ids = [x.get("contentDetails", {}).get("videoId")
               for x in lote.get("items", [])]
        ids = [x for x in ids if x]
        if ids:
            videos = youtube.videos().list(
                part="snippet,status", id=",".join(ids)
            ).execute()
            for video in videos.get("items", []):
                coincide = es_duplicado(video.get("snippet", {}), tema_id, formato)
                if coincide:
                    video_id = video.get("id", "desconocido")
                    raise RuntimeError(
                        "BLOQUEADO: ya existe un vídeo de este tema en el canal: "
                        + video_id + ". Revisar YouTube Studio antes de continuar."
                    )
        pagina = lote.get("nextPageToken")
        if not pagina:
            return
    raise RuntimeError(
        "Más de 600 vídeos encontrados. Revisar duplicados manualmente; "
        "la búsqueda automática no puede asegurar unicidad."
    )

def subir_privado(youtube,plan,titulo,descripcion,mp4,miniatura):
    peticion=youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet":{
                "title":titulo,
                "description":descripcion[:4800],
                "categoryId":"20",
                "defaultLanguage":"es",
                "defaultAudioLanguage":"es",
                "tags":normalizar_etiquetas(
                    plan.get("etiquetas", ["videojuegos", "gaming", "Píxel Feroz"]),
                    plan["tema_id"], plan["formato"]
                )
            },
            "status":{
                "privacyStatus":"private",
                "selfDeclaredMadeForKids":False,
                "embeddable":True,
                "license":"youtube"
            }
        },
        media_body=MediaFileUpload(str(mp4),mimetype="video/mp4",
                                  resumable=True,chunksize=8*1024*1024)
    )
    respuesta=None
    while respuesta is None:
        _,respuesta=peticion.next_chunk()
    video_id=respuesta.get("id")
    if not video_id:
        raise RuntimeError("YouTube no devolvió ID de vídeo")
    print("Vídeo recibido por YouTube:", video_id, flush=True)
    # Registrar el ID inmediatamente antes de otras llamadas externas.
    # Si la subida ya funcionó, un error de miniatura o verificación no debe
    # ocultar que puede existir un vídeo privado en el canal.
    res = {
        "video_id": video_id,
        "url": "https://www.youtube.com/watch?v=" + video_id,
        "estado": "pendiente_verificacion",
        "privacidad_verificada": None,
        "tema_id": plan["tema_id"],
        "formato": plan["formato"],
        "fecha": datetime.now(timezone.utc).isoformat()
    }
    resultado = OUT / "youtube_resultado.json"
    resultado.write_text(
        json.dumps(res, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    verificado = False
    for intento in range(4):
        detalle = youtube.videos().list(part="status", id=video_id).execute()
        items = detalle.get("items", [])
        if items:
            privacidad = items[0].get("status", {}).get("privacyStatus")
            if privacidad == "private":
                verificado = True
                break
            if privacidad in ("public", "unlisted"):
                raise RuntimeError(
                    "ALERTA: la privacidad no es privada. Revisar inmediatamente: "
                    + video_id
                )
        if intento < 3:
            time.sleep(4)
    if not verificado:
        raise RuntimeError(
            "YouTube recibió el vídeo " + video_id
            + " pero no se confirmó privacidad. Consultar YouTube Studio; "
            "no repetir la subida sin verificar su existencia."
        )

    res["estado"] = "subido"
    res["privacidad_verificada"] = "private"
    miniatura_confirmada = False
    # Para Shorts la API exige esperar a que YouTube termine de procesarlos.
    # La ausencia de permiso no autoriza publicar sin miniatura: se registra
    # la incidencia en el historial y el workflow dará error después.
    procesado = plan["formato"] != "short"
    if not procesado:
        for intento in range(15):
            estado = youtube.videos().list(
                part="processingDetails", id=video_id
            ).execute()
            elementos = estado.get("items", [])
            progreso = (
                elementos[0].get("processingDetails", {}).get("processingStatus")
                if elementos else None
            )
            if progreso == "succeeded":
                procesado = True
                break
            if progreso in ("failed", "terminated"):
                break
            if intento < 14:
                time.sleep(8)
    if procesado:
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(
                    str(miniatura), mimetype="image/jpeg"
                )
            ).execute()
            miniatura_confirmada = True
            print("Miniatura personalizada aceptada por YouTube", flush=True)
        except HttpError as exc:
            print(
                "::warning::Miniatura no aplicada por YouTube. Vídeo "
                + video_id + " sigue PRIVADO. Error HTTP "
                + str(exc.resp.status)
                + ". Comprueba verificación del canal y los permisos.",
                flush=True
            )
    else:
        print(
            "::warning::YouTube aún no terminó de procesar el Short "
            + video_id + ". La miniatura queda pendiente.",
            flush=True
        )
    res["miniatura_confirmada"] = miniatura_confirmada
    resultado.write_text(
        json.dumps(res, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    print("PRIVADO confirmado por YouTube:", res["url"], flush=True)
    return res


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--formato",choices=("short","largo"),required=True)
    args=p.parse_args()
    if os.getenv("PF_SUBIR_PRIVADO")!="SI":
        raise RuntimeError("Subida bloqueada: PF_SUBIR_PRIVADO debe ser SI")
    plan,titulo,descripcion,mp4,miniatura=comprobar_archivos(args.formato)
    # Un fallo posterior a la subida no debe provocar reintentos automáticos.
    if (OUT/"youtube_resultado.json").exists():
        raise RuntimeError("Ya hay resultado anterior; impide subida duplicada")
    yt=cliente()
    verificar_identidad(yt)
    rechazar_subida_duplicada(yt,plan["tema_id"],plan["formato"])
    subir_privado(yt,plan,titulo,descripcion,mp4,miniatura)


if __name__=="__main__":
    main()
