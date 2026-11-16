#!/usr/bin/env python3
"""Vista previa de locutores con acento español de España (es-ES).

Usa Gemini 3.8 Flash TTS con la misma GEMINI_API_KEY que ya está almacenada
en GitHub Actions. Nunca sube vídeos ni añade credenciales al repositorio.

No sustituye el motor de producción hasta validar una muestra con escucha.
"""
import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.request
import wave
from pathlib import Path

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
MODEL = "gemini-3.8-flash-tts"
VOCES = ("Charon", "Achird")

MUESTRA = (
    "¿Te has fijado en la cantidad de novedades que están llegando "
    "al mundo de los videojuegos? En Píxel Feroz repasamos GTA seis, "
    "los próximos lanzamientos y lo que realmente está confirmado. "
    "Sin rumores absurdos, sin perder el tiempo y con las noticias "
    "que más te interesan. ¡Suscríbete para no perderte nada!"
)
ESTILO = (
    "Español peninsular de España (es-ES), acento castellano neutro "
    "de locutor nacido y criado en España. Voz masculina adulta, natural, "
    "cercana y expresiva. Diccion española con distincion clara de los "
    "sonidos de 'cena', 'zapato' y 'silla'; nunca acento latinoamericano. "
    "Estilo de creador de contenido de videojuegos, como una persona "
    "hablando con su audiencia: ritmo conversacional ligeramente ágil, "
    "entonación variada y pausas naturales. Nada de voz robótica, "
    "tono publicitario exagerado o radio solemne."
)


def peticion_audio(texto, voz):
    if voz not in VOCES:
        raise ValueError("Voz no admitida")
    if not isinstance(texto, str) or not 10 <= len(texto) <= 1400:
        raise ValueError("Texto de voz de longitud incorrecta")
    return {
        "model": MODEL,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": texto,
                "annotations": [
                    {"type": "speech_metadata", "style": ESTILO},
                ],
            }],
        }],
        "response_format": {"type": "audio", "mime_type": "audio/wav"},
        "generation_config": {
            "speech_config": [{"voice": voz}],
        },
    }


def extraer_audio(respuesta):
    """Extrae el último bloque de audio del JSON REST de Interactions.

    Interactions REST devuelve pasos de salida: steps[].content[].data.
    El SDK de Google presenta ese bloque como interaction.output_audio,
    pero esta propiedad de conveniencia NO existe en la respuesta REST.
    """
    if not isinstance(respuesta, dict):
        raise RuntimeError("Gemini TTS no devolvió un objeto JSON")
    contenedor = respuesta.get("interaction", respuesta)
    candidatos = []
    pasos = contenedor.get("steps", []) if isinstance(contenedor, dict) else []
    if isinstance(pasos, list):
        for paso in pasos:
            if not isinstance(paso, dict) or paso.get("type") != "model_output":
                continue
            contenidos = paso.get("content", [])
            if not isinstance(contenidos, list):
                continue
            for contenido in contenidos:
                if isinstance(contenido, dict) and contenido.get("type") == "audio":
                    candidatos.append(contenido.get("data"))
    # También tolerar la propiedad de conveniencia del SDK cuando se
    # comprueba con una respuesta simulada, sin depender de ella en REST.
    bloque = (
        contenedor.get("output_audio") or contenedor.get("outputAudio")
        if isinstance(contenedor, dict) else None
    )
    if isinstance(bloque, dict):
        candidatos.append(bloque.get("data"))
    for encoded in reversed(candidatos):
        if not isinstance(encoded, str):
            continue
        try:
            audio = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error):
            continue
        if audio[:4] == b"RIFF" and audio[8:12] == b"WAVE":
            return audio
    estado = str(contenedor.get("status", "sin audio")) if isinstance(contenedor, dict) else ""
    # Solo estado, nunca imprimir la respuesta que puede contener datos.
    raise RuntimeError(
        "Gemini TTS no devolvió audio WAV en steps[].content[].data."
        " Estado: " + estado[:70]
    )


def sintetizar(texto, voz, destino, clave=None):
    clave = clave or os.environ.get("GEMINI_API_KEY", "")
    if not clave:
        raise RuntimeError("No existe GEMINI_API_KEY en los Secrets de Actions")
    body = json.dumps(
        peticion_audio(texto, voz), ensure_ascii=False
    ).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": clave,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=125) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        # No revelar cuerpo de error: podría mostrar datos de la solicitud.
        raise RuntimeError(
            "Gemini TTS respondió HTTP "
            + str(error.code) + ". Comprueba acceso al modelo y cuota."
        ) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("No se recibió audio de Gemini TTS") from None

    audio = extraer_audio(data)

    if not (10000 <= len(audio) <= 20_000_000):
        raise RuntimeError("Respuesta de audio vacía o demasiado grande")
    if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        raise RuntimeError("El audio de Gemini no es WAV válido")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp")
    try:
        temporal.write_bytes(audio)
        with wave.open(str(temporal), "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                raise RuntimeError("Gemini TTS no devolvió WAV PCM mono 16 bit")
            segundos = wf.getnframes() / wf.getframerate()
        if not 2 <= segundos <= 90:
            raise RuntimeError("Duración inadecuada de la narración de prueba")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    print("Muestra de voz castellana creada:", voz,
          "| duración:", round(segundos, 1), "segundos", flush=True)
    return segundos


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--voz", choices=VOCES, required=True)
    p.add_argument("--salida", type=Path, required=True)
    args = p.parse_args()
    sintetizar(MUESTRA, args.voz, args.salida)
    print("No se han creado ni publicado vídeos.")


if __name__ == "__main__":
    main()
