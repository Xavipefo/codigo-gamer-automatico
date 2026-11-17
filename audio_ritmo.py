"""Acelera suavemente WAV PCM16 sin cambiar el tono (FFmpeg atempo).

Aplicar DESPUÉS de generar Qwen, nunca al guion. Afecta a audio y,
gracias a duracion_audio, también a la duración de los clips del vídeo.
"""
import math
import subprocess
import wave
from pathlib import Path


def segundos_wav(archivo):
    with wave.open(str(archivo), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError("Solo se admiten WAV mono PCM16")
        return wav.getnframes() / wav.getframerate()


def ajustar_ritmo_wav(archivo, factor):
    archivo = Path(archivo)
    factor = float(factor)
    if not math.isfinite(factor) or not 1.0 <= factor <= 1.20:
        raise ValueError("La velocidad debe estar entre 1.0 y 1.20")
    anterior = segundos_wav(archivo)
    if factor == 1.0:
        return anterior
    nuevo = archivo.with_suffix(".ritmo.tmp.wav")
    try:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-y", "-i", str(archivo), "-af", f"atempo={factor:.3f}",
             "-ac", "1", "-c:a", "pcm_s16le", str(nuevo)],
            check=True, capture_output=True, text=True, timeout=90,
        )
        final = segundos_wav(nuevo)
        # Una pequeña tolerancia es normal en el filtro atempo.
        if not 0.95 * (anterior / factor) <= final <= 1.05 * (anterior / factor):
            raise ValueError("Duración del WAV acelerado incoherente")
        nuevo.replace(archivo)
        return final
    finally:
        nuevo.unlink(missing_ok=True)
