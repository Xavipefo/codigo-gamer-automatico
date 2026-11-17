#!/usr/bin/env python3
"""Muestras 100 % locales de Qwen3-TTS para Píxel Feroz.

NO usa Gemini/Azure, NO clona Achird/Charon y NO sube a YouTube.
El modelo y el texto son públicos. La generación utiliza CPU en GitHub.

Modelos oficiales Apache-2.0:
  ligero: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
  diseno: Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
"""
import argparse
import os
import wave
from pathlib import Path

MODELOS = {
    "ligero": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    "diseno": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
}
PERFILES = {
    "presentador": (
        "An original Spanish-speaking adult male voice from Spain, "
        "Castilian Spanish accent with clear distinction between z/c and s, "
        "warm medium-low pitch, youthful videogame host, energetic but not "
        "shouting, natural conversational pacing, gentle breaths and pauses. "
        "No Latin American accent, no announcer or robotic intonation. "
        "Do not imitate any existing speaker."
    ),
    "analista": (
        "An original Spanish-speaking adult male voice from Spain, "
        "Castilian Spanish accent with clear distinction between z/c and s, "
        "calm medium-low pitch, confident and reflective gaming analyst, "
        "subtle emotion, natural pauses, conversational rather than formal. "
        "No Latin American accent and no imitation of a real speaker."
    ),
}
TEXTO = (
    "Ojo a esto. GTA seis sigue dando mucho que hablar. "
    "Pero en Píxel Feroz queremos separar lo que está confirmado "
    "de los rumores. Hoy repasamos las novedades de los videojuegos."
)
PRESET = {"presentador": "Ryan", "analista": "Aiden"}


def configurar(modelo, perfil, destino):
    if modelo not in MODELOS:
        raise ValueError("Modelo no admitido")
    if perfil not in PERFILES:
        raise ValueError("Perfil no admitido")
    destino = Path(destino)
    if destino.suffix.lower() != ".wav":
        raise ValueError("La muestra debe guardarse en WAV")
    return destino


def generar(modelo, perfil, destino, motor=None):
    """Carga un checkpoint una sola vez en main y genera audio original."""
    destino = configurar(modelo, perfil, destino)
    if motor is None:
        raise ValueError("Falta el motor local Qwen3-TTS")
    if modelo == "ligero":
        muestras, frecuencia = motor.generate_custom_voice(
            text=TEXTO, language="Spanish", speaker=PRESET[perfil]
        )
    else:
        muestras, frecuencia = motor.generate_voice_design(
            text=TEXTO, language="Spanish", instruct=PERFILES[perfil]
        )

    if not muestras or frecuencia <= 0:
        raise RuntimeError("El modelo libre no devolvió audio")
    import numpy as np
    import soundfile as sf
    audio = np.asarray(muestras[0])
    if audio.ndim != 1 or not np.isfinite(audio).all():
        raise RuntimeError("Audio inválido o multicanal")
    duracion = len(audio) / frecuencia
    if not 2 <= duracion <= 90:
        raise RuntimeError("Audio demasiado breve/largo para la prueba")
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp")
    try:
        sf.write(str(temporal), audio, frecuencia, format="WAV", subtype="PCM_16")
        with wave.open(str(temporal), "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise RuntimeError("No se pudo generar WAV mono PCM16")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    print(
        "Qwen libre:", modelo, "/", perfil,
        "| segundos:", round(duracion, 1),
        "| muestra local, sin subir a YouTube", flush=True
    )
    return duracion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", choices=sorted(MODELOS), default="ligero")
    parser.add_argument("--salida", type=Path, default=Path("voces_libres"))
    args = parser.parse_args()

    import torch
    from qwen_tts import Qwen3TTSModel

    torch.set_num_threads(min(4, max(1, os.cpu_count() or 1)))
    torch.manual_seed(2026)
    print(
        "Cargando modelo libre desde Hugging Face:", MODELOS[args.modelo],
        "| CPU | licencia Apache-2.0", flush=True,
    )
    motor = Qwen3TTSModel.from_pretrained(
        MODELOS[args.modelo],
        device_map="cpu",
        dtype=torch.float32,
        attn_implementation="sdpa",
    )
    for perfil in ("presentador", "analista"):
        generar(args.modelo, perfil, args.salida / f"qwen_{args.modelo}_{perfil}.wav",
                motor=motor)
    print("Dos muestras completas. No se ha generado ni subido ningún vídeo.")


if __name__ == "__main__":
    main()
