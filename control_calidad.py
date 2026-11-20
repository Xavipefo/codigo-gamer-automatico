#!/usr/bin/env python3
"""Verifica técnicamente el vídeo sin enviarlo ni modificar YouTube.

No sustituye la revisión editorial, musical ni de derechos de autor.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image
from preparar_contenido import validar_tema
from voz_produccion import elegir_voz, CONFIG

BASE = Path(__file__).resolve().parent
OUT = BASE / "salida"
THEMES = BASE / "temas_verificados.json"


def comprobar(formato):
    if formato not in ("short", "largo"):
        raise ValueError("Formato desconocido")
    if not shutil.which("ffprobe"):
        raise RuntimeError("Se necesita ffprobe")
    plan = json.loads((OUT / "plan.json").read_text(encoding="utf-8"))
    if plan.get("formato") != formato:
        raise ValueError("El formato del vídeo no coincide con el plan")
    if plan.get("canal") != "Píxel Feroz":
        raise ValueError("El plan no corresponde a Píxel Feroz")
    if plan.get("publicacion_automatica") is not False:
        raise ValueError("La publicación automática debe estar desactivada")
    if plan.get("estado") != "BORRADOR_PENDIENTE_REVISION":
        raise ValueError("Estado editorial inválido")
    if plan.get("revision_pendiente") is not True:
        raise ValueError("Debe conservar la revisión editorial pendiente")
    if plan.get("narrador_sintetico") is not True:
        raise ValueError("El vídeo debe identificar una narración sintética")
    if plan.get("narrador_voz") != elegir_voz(formato):
        raise ValueError("La voz no coincide con el reparto editorial")


    temas = json.loads(THEMES.read_text(encoding="utf-8"))
    tema = next((t for t in temas if t.get("id") == plan.get("tema_id")), None)
    if tema is None:
        raise ValueError("El tema no existe en la lista editorial")
    validar_tema(tema)  # Comprueba fecha, estado y dominios de cada fuente.
    guion = (OUT / "guion.txt").read_text(encoding="utf-8").strip()
    if hashlib.sha256(guion.encode("utf-8")).hexdigest() != plan.get("huella_guion"):
        raise ValueError("El texto narrado ha cambiado después de aprobar el plan")
    if len(guion.split()) < (45 if formato == "short" else 650):
        raise ValueError("Guion demasiado corto para el formato")
    if not 5 <= len(plan.get("titulo_propuesto", "")) <= 100:
        raise ValueError("Título fuera del límite permitido")
    descripcion = (OUT / "descripcion.txt").read_text(encoding="utf-8")
    for hecho in tema["hechos"]:
        if hecho["fuente"] not in descripcion:
            raise ValueError("La descripción no incluye una fuente del tema")
    if any(x in descripcion for x in (
        "Identificador editorial:", "Formato editorial:",
        "PF-ID:", "PF-FORMATO:"
    )):
        raise ValueError("La descripción contiene metadatos editoriales internos")

    video = OUT / (
        "pixel_feroz_short.mp4" if formato == "short"
        else "pixel_feroz_largo.mp4"
    )
    if not video.is_file() or video.stat().st_size < 20_000:
        raise ValueError("Vídeo pequeño, ausente o vacío")

    proceso = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format",
         "-of", "json", str(video)],
        check=True, capture_output=True, text=True, timeout=30
    )
    info = json.loads(proceso.stdout)
    streams = info.get("streams", [])
    vis = next((x for x in streams if x.get("codec_type") == "video"), None)
    aud = next((x for x in streams if x.get("codec_type") == "audio"), None)
    if not vis or not aud:
        raise ValueError("Falta una pista de vídeo o audio")
    expected = (720, 1280) if formato == "short" else (1280, 720)
    if (vis.get("width"), vis.get("height")) != expected:
        raise ValueError("Resolución incorrecta")
    if vis.get("codec_name") != "h264" or aud.get("codec_name") != "aac":
        raise ValueError("Se requiere vídeo H264 y audio AAC")
    duracion = float(info.get("format", {}).get("duration", 0))
    if not math.isfinite(duracion):
        raise ValueError("La duración del MP4 no es finita")
    limites = (10, 180) if formato == "short" else (180, 1200)
    if not limites[0] <= duracion <= limites[1]:
        raise ValueError(f"Duración fuera de rango: {duracion:.1f} segundos")
    video_seg = float(vis.get("duration") or duracion)
    audio_seg = float(aud.get("duration") or duracion)
    if abs(video_seg - audio_seg) > 1.0:
        raise ValueError(
            f"Desincronización: vídeo {video_seg:.2f}s, audio {audio_seg:.2f}s"
        )

    ritmo_pf41 = None
    if (formato == "short"
            and plan.get("estilo_retencion") == "PF-41-ganchos-directos-planos-3s"
            and os.environ.get("PF_ROCKSTAR_MEDIA") == "1"):
        informe = OUT / "informe_ritmo_pf41.json"
        if not informe.is_file():
            raise ValueError(
                "PF-41: falta informe de subplanos del Short"
            )
        ritmo_pf41 = json.loads(informe.read_text(encoding="utf-8"))
        if (ritmo_pf41.get("tema_id") != plan["tema_id"]
                or ritmo_pf41.get("primer_plano") != "foto"
                or ritmo_pf41.get("numero_planos", 0) < 2):
            raise ValueError(
                "PF-41: no hay suficientes planos oficiales en el vídeo"
            )
        if not all(
            0 < t["segundos"] <= 3.801 and t.get("medio") == "foto"
            for t in ritmo_pf41.get("planos", [])
        ):
            raise ValueError(
                "PF-41: un plano supera 3,8 segundos o no es oficial"
            )
        if abs(float(ritmo_pf41["duracion_segundos"]) - duracion) > 1.0:
            raise ValueError(
                "PF-41: diferencia entre montaje y duración informada"
            )

    miniatura = OUT / "miniatura.jpg"
    if not miniatura.is_file() or miniatura.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Miniatura ausente o demasiado grande")
    with Image.open(miniatura) as im:
        if im.format != "JPEG" or im.size != expected:
            raise ValueError("Formato o dimensiones de miniatura no válidos")
        im.verify()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    motor = config.get("motor_voz", "gemini-3.8-flash-tts")
    forzado = os.environ.get("PF_TTS_PROVIDER", "").strip().lower()
    if forzado == "azure":
        motor = "azure-neural"
    elif forzado == "gemini":
        motor = "gemini-3.8-flash-tts"
    elif forzado == "qwen":
        motor = "qwen3-tts-0.6b"
    if motor == "azure-neural":
        voz_real = (
            "es-ES-AlvaroNeural" if formato == "short"
            else "es-ES-ArnauNeural"
        )
    elif motor == "qwen3-tts-0.6b":
        voz_real = "Qwen3-TTS 0.6B / Ryan"
    else:
        voz_real = plan["narrador_voz"]

    resultado = {
        "canal": "Píxel Feroz",
        "tema": plan["tema_id"],
        "formato": formato,
        "segundos": round(duracion, 2),
        "resolucion": list(expected),
        "audio": "aac",
        "video": "h264",
        "fuentes_referenciadas": len(tema["hechos"]),
        "sincronizacion_tecnica": True,
        "motor_voz": motor,
        "narrador_voz": plan["narrador_voz"],
        "voz_real": voz_real,
        "narrador_sintetico": True,
        "revision_editorial_pendiente": True,
        "listo_para_subida_privada": True,
        "informe_ritmo_pf41": ritmo_pf41 and {
            "numero_planos": ritmo_pf41["numero_planos"],
            "plano_maximo_segundos": ritmo_pf41["plano_maximo_segundos"],
            "duracion_cierre_segundos": ritmo_pf41["duracion_cierre_segundos"],
        },
    }
    (OUT / "calidad.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--formato", choices=("short", "largo"), required=True)
    args = parser.parse_args()
    comprobar(args.formato)
