#!/usr/bin/env python3
"""Reparar miniatura de vídeo YA subido, SIN volver a subir MP4."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from motor_video import crear_miniatura
from subir_youtube_privado import cliente, verificar_identidad

BASE = Path(__file__).resolve().parent
HISTORIAL = BASE / "historial_publicados.json"
TEMAS = BASE / "temas_verificados.json"
CONFIG = BASE / "config.json"
MINIATURA = BASE / "salida" / "miniatura.jpg"


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--video-id", default="", help="Opcional, usa el primero pendiente si vacío")
    args = cli.parse_args()
    registros = json.loads(HISTORIAL.read_text(encoding="utf-8"))
    if not isinstance(registros, list):
        raise ValueError("El historial no es una lista JSON")
    pendientes = [
        x for x in registros
        if x.get("estado") == "subido"
        and x.get("privacidad_verificada") == "private"
        and x.get("miniatura_confirmada") is not True
        and (not args.video_id or x.get("video_id") == args.video_id)
    ]
    if not pendientes:
        raise ValueError("No hay miniaturas pendientes de reparación")
    dato = pendientes[0]
    temas = json.loads(TEMAS.read_text(encoding="utf-8"))
    tema = next((x for x in temas if x.get("id") == dato["tema_id"]), None)
    if tema is None:
        raise ValueError("El tema del vídeo ya no existe en el archivo")
    etiqueta = tema.get("texto_miniatura", tema["titulo"])
    MINIATURA.parent.mkdir(parents=True, exist_ok=True)
    crear_miniatura(etiqueta, dato["formato"], MINIATURA)

    yt = cliente()
    verificar_identidad(yt)
    respuesta = yt.videos().list(
        part="snippet,status,processingDetails", id=dato["video_id"]
    ).execute()
    videos = respuesta.get("items", [])
    canal_id = json.loads(CONFIG.read_text(encoding="utf-8"))["youtube_channel_id"]
    if len(videos) != 1:
        raise RuntimeError("El vídeo no está disponible en el canal autorizado")
    video = videos[0]
    if video.get("snippet", {}).get("channelId") != canal_id:
        raise RuntimeError("El vídeo pertenece a otro canal")
    if video.get("status", {}).get("privacyStatus") != "private":
        raise RuntimeError("No se permite actuar sobre vídeos que no sean privados")
    procesado = video.get("processingDetails", {}).get("processingStatus")
    if dato["formato"] == "short" and procesado != "succeeded":
        raise RuntimeError("El Short todavía no ha terminado su procesamiento")

    yt.thumbnails().set(
        videoId=dato["video_id"],
        media_body=MediaFileUpload(str(MINIATURA), mimetype="image/jpeg"),
    ).execute()
    dato["miniatura_confirmada"] = True
    dato["miniatura_fecha_utc"] = datetime.now(timezone.utc).isoformat()
    HISTORIAL.write_text(
        json.dumps(registros, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Miniatura personalizada aplicada al vídeo privado:", dato["video_id"])
    print("No se ha vuelto a subir el MP4.")


if __name__ == "__main__":
    main()
