#!/usr/bin/env python3
"""Narrador local Qwen3-TTS Ryan para Píxel Feroz.

CPU, modelo público Apache-2.0, sin API de voz ni cuotas externas.
Carga los pesos UNA SOLA VEZ por vídeo (todas las escenas).
No se generan artifacts con guiones ni WAV de contenido privado.
"""
import json
import os
import wave
from pathlib import Path

from voz_produccion import preparar_lectura, elegir_voz, NarradorGemini
from voz_qwen_libre import MODELOS
from audio_ritmo import ajustar_ritmo_wav

MODELO_LOCAL = MODELOS["ligero"]
VOZ_LOCAL = "Ryan"


class NarradorQwen:
    def __init__(self, formato, plan, motor=None):
        if formato not in ("short", "largo"):
            raise ValueError("Formato de vídeo no admitido")
        if elegir_voz(formato, plan) != VOZ_LOCAL:
            raise ValueError("El plan de Qwen requiere la voz Ryan")
        self.formato = formato
        self.proveedor = "qwen"
        self.voz = VOZ_LOCAL
        self.voz_real = f"Qwen3-TTS 0.6B / {VOZ_LOCAL}"
        self.peticiones = 0
        self.recuperados = 0
        self.segundos = 0.0
        self.max_peticiones = 12 if formato == "short" else 45
        config = json.loads(
            (Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8")
        )
        self.factor_ritmo = (
            float(config.get("velocidad_ryan_largos", 1.0))
            if formato == "largo" else 1.0
        )
        if not 1.0 <= self.factor_ritmo <= 1.20:
            raise ValueError("Velocidad de Ryan fuera de los límites seguros")
        if motor is None:
            import torch
            from qwen_tts import Qwen3TTSModel

            torch.set_num_threads(min(4, max(1, os.cpu_count() or 1)))
            torch.manual_seed(2026)
            print(
                "Cargando Qwen3-TTS 0.6B en CPU una sola vez para el vídeo.",
                flush=True,
            )
            motor = Qwen3TTSModel.from_pretrained(
                MODELO_LOCAL,
                device_map="cpu",
                dtype=torch.float32,
                attn_implementation="sdpa",
            )
        self.motor = motor
        print(
            "Narrador Qwen local:", VOZ_LOCAL,
            "| formato:", formato, "| sin API de audio", flush=True,
        )

    def narrar(self, texto, ruta):
        import numpy as np
        import soundfile as sf

        if not isinstance(texto, str) or not 10 <= len(texto) <= 1400:
            raise ValueError("Texto fuera del límite permitido")
        ruta = Path(ruta)
        esperado_minimo = max(2.0, len(texto.split()) / 5.0)
        recuperado = NarradorGemini._recuperar_wav(ruta, esperado_minimo)
        if recuperado is not None:
            self.recuperados += 1
            self.segundos += recuperado
            return recuperado
        ruta.unlink(missing_ok=True)

        if self.peticiones >= self.max_peticiones:
            raise RuntimeError("Máximo de bloques Qwen por vídeo agotado")
        self.peticiones += 1
        print(
            "Qwen local: bloque", self.peticiones,
            "| palabras", len(texto.split()), flush=True,
        )
        muestras, frecuencia = self.motor.generate_custom_voice(
            text=preparar_lectura(texto),
            language="Spanish",
            speaker=VOZ_LOCAL,
        )
        if len(muestras) != 1 or frecuencia <= 0:
            raise RuntimeError("Qwen no generó un único bloque de voz")
        audio = np.asarray(muestras[0])
        if audio.ndim != 1 or not np.isfinite(audio).all():
            raise RuntimeError("Qwen devolvió audio inválido")
        segundos = len(audio) / frecuencia
        if not esperado_minimo <= segundos <= 90:
            raise RuntimeError(
                "Qwen generó un bloque incompleto o demasiado largo. "
                "No se subirá ningún vídeo con voz truncada."
            )
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta.with_suffix(".tmp")
        try:
            sf.write(
                str(temporal), audio, frecuencia, format="WAV", subtype="PCM_16"
            )
            with wave.open(str(temporal), "rb") as wav:
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                    raise RuntimeError("Qwen no generó PCM mono de 16 bits")
            temporal.replace(ruta)
        finally:
            temporal.unlink(missing_ok=True)

        if self.factor_ritmo > 1.0:
            segundos = ajustar_ritmo_wav(ruta, self.factor_ritmo)
            print(
                "Ryan: velocidad final", self.factor_ritmo,
                "x, tono conservado (atempo).", flush=True
            )
        self.segundos += segundos
        if self.segundos > (180 if self.formato == "short" else 1200):
            raise RuntimeError("Duración total de narración fuera de límite")
        return segundos
