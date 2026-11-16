#!/usr/bin/env python3
"""Prueba privada de voces españolas de Azure AI Speech (nivel F0 compatible).

No clona voces ni sube vídeos. Genera un WAV PCM mono a 24 kHz para
comparar dos locutores antes de escoger el nuevo motor de producción.

Requiere GitHub Secrets AZURE_SPEECH_KEY y AZURE_SPEECH_REGION. No imprimir
claves, respuestas de servidor, URLs de petición ni texto confidencial.
"""
import argparse
import io
import os
import re
import urllib.error
import urllib.request
import wave
from html import escape
from pathlib import Path

VOCES = {
    "Alvaro": "es-ES-AlvaroNeural",
    "Arnau": "es-ES-ArnauNeural",
}

MUESTRA = (
    "Atención a esto: GTA seis sigue despertando muchísima curiosidad, "
    "pero aquí vamos a separar los hechos confirmados de los rumores. "
    "En Píxel Feroz te contamos las novedades de los videojuegos "
    "con claridad, sin exageraciones y con información contrastada. "
    "Si te gusta conocer todos los detalles, suscríbete para estar al día."
)


def validar_region(region):
    if not re.fullmatch(r"[a-z][a-z0-9]{2,20}", region or ""):
        raise ValueError("Región de Azure no válida; usa la región corta, por ejemplo westeurope")
    return region


def crear_ssml(texto, voz):
    if voz not in VOCES:
        raise ValueError("Voz Azure no reconocida")
    if not isinstance(texto, str) or not 10 <= len(texto) <= 4000:
        raise ValueError("Texto fuera de límites de Azure TTS")
    velocidad = "+3%" if voz == "Alvaro" else "-3%"
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="es-ES">'
        f'<voice name="{VOCES[voz]}">'
        f'<prosody rate="{velocidad}">{escape(texto, quote=False)}</prosody>'
        '</voice></speak>'
    )


def sintetizar(texto, voz, destino, clave=None, region=None):
    clave = clave or os.environ.get("AZURE_SPEECH_KEY", "").strip()
    region = validar_region(
        region or os.environ.get("AZURE_SPEECH_REGION", "").strip()
    )
    if not clave:
        raise RuntimeError("Falta AZURE_SPEECH_KEY")
    ssml = crear_ssml(texto, voz)
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    req = urllib.request.Request(
        url,
        data=ssml.encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/ssml+xml",
            "Ocp-Apim-Subscription-Key": clave,
            "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
            "User-Agent": "PixelFeroz-VoicePreview/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=100) as respuesta:
            # La muestra es corta; no guardar respuestas arbitrariamente grandes.
            audio = respuesta.read(14_000_001)
    except urllib.error.HTTPError as exc:
        # El cuerpo puede ser sensible: nunca leerlo ni mostrarlo en los logs.
        raise RuntimeError(
            f"Azure Speech respondió HTTP {exc.code}. "
            "Comprueba el recurso, la región, la cuota F0 y las credenciales."
        ) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        raise RuntimeError(
            "Azure Speech no respondió. Revisa la conexión y región."
        ) from None
    if not 10000 <= len(audio) <= 14_000_000:
        raise RuntimeError("Azure Speech devolvió un audio vacío o demasiado largo")
    if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise RuntimeError("Azure Speech no devolvió audio WAV")

    try:
        with wave.open(io.BytesIO(audio), "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise RuntimeError("Azure no devolvió PCM mono 16 bits")
            if wav.getframerate() != 24000:
                raise RuntimeError("La muestra Azure no está a 24 kHz")
            duracion = wav.getnframes() / wav.getframerate()
    except wave.Error:
        raise RuntimeError("WAV Azure no válido") from None
    if not 2 <= duracion <= 120:
        raise RuntimeError("Duración Azure incorrecta")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp")
    try:
        temporal.write_bytes(audio)
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    print(
        "Muestra Azure creada:", voz, "| duración:",
        round(duracion, 1), "segundos", flush=True,
    )
    return duracion


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voz", choices=tuple(VOCES), required=True)
    p.add_argument("--salida", required=True, type=Path)
    args = p.parse_args()
    sintetizar(MUESTRA, args.voz, args.salida)
    print("Solo muestra de voz: ningún vídeo ha sido subido.")


if __name__ == "__main__":
    main()
