#!/usr/bin/env python3
"""Subida de vídeo exclusivamente PRIVADO con comprobación de canal y OAuth.

No hay opción de subir público o programar vídeo. Fallará si faltan credenciales.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

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
    esperado=os.getenv("YOUTUBE_CHANNEL_ID","").strip()
    if not esperado:
        raise RuntimeError("Falta YOUTUBE_CHANNEL_ID")
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
                "tags":["videojuegos","gaming","GTA VI","Píxel Feroz"]
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
    print("Vídeo subido:",video_id,flush=True)
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(miniatura),mimetype="image/jpeg")
        ).execute()
        print("Miniatura subida",flush=True)
    except HttpError as e:
        # Si la miniatura falla, el MP4 ya existe. NO repetir la subida.
        print("AVISO miniatura: vídeo subido pero miniatura no configurada:",e,flush=True)
    detalle=youtube.videos().list(part="status",id=video_id).execute()
    items=detalle.get("items",[])
    if not items or items[0].get("status",{}).get("privacyStatus")!="private":
        raise RuntimeError("No se pudo verificar privacidad PRIVATE; comprobar en YouTube Studio")
    res={
        "video_id":video_id,
        "url":"https://www.youtube.com/watch?v="+video_id,
        "estado":"subido",
        "privacidad_verificada":"private",
        "tema_id":plan["tema_id"],
        "formato":plan["formato"],
        "fecha":datetime.now(timezone.utc).isoformat()
    }
    (OUT/"youtube_resultado.json").write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRIVADO confirmado por YouTube:",res["url"],flush=True)
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
    subir_privado(yt,plan,titulo,descripcion,mp4,miniatura)


if __name__=="__main__":
    main()
