#!/usr/bin/env python3
"""Producción de audio es-ES con dos voces, según formato del vídeo.

Achird: noticias y Shorts. Charon: vídeos largos y análisis.
Cada vídeo tiene un narrador constante, no cambios aleatorios de locutor.
La voz final se genera mediante la API de Gemini desde GitHub Secrets.

Nunca publica vídeos. Falla con diagnóstico antes del upload si no puede
producir una narración natural; no sustituye silenciosamente por una
voz robótica que el usuario haya rechazado.
"""
import json
import os
from pathlib import Path

from voz_gemini_castellano import VOCES, sintetizar

RAIZ = Path(__file__).resolve().parent
CONFIG = RAIZ / "config.json"
DEFAULT = {"short": "Achird", "largo": "Charon"}


def elegir_voz(formato, plan=None, config=None):
    if formato not in DEFAULT:
        raise ValueError("Formato audiovisual no reconocido")
    if config is None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("La configuración de voces no es válida")
    mapeo = config.get("voces_por_formato", DEFAULT)
    if not isinstance(mapeo, dict):
        raise ValueError("voces_por_formato debe ser un objeto")
    voz_config = mapeo.get(formato, DEFAULT[formato])
    voz = (plan or {}).get("narrador_voz", voz_config)
    if voz not in VOCES:
        raise ValueError("El narrador debe ser Achird o Charon")
    if (plan or {}).get("formato") not in (None, formato):
        raise ValueError("El narrador y el formato no coinciden")
    return voz


def estimar_consumo(escenas, formato):
    """Límites conservadores previos a llamadas facturables TTS."""
    if formato not in DEFAULT:
        raise ValueError("Formato no permitido")
    max_escenas = 12 if formato == "short" else 45
    max_caracteres = 1800 if formato == "short" else 16000
    if not 1 <= len(escenas) <= max_escenas:
        raise ValueError(
            "Demasiadas escenas para narración natural en " + formato
        )
    total = 0
    for escena in escenas:
        texto = escena["texto"]
        if not isinstance(texto, str) or not 10 <= len(texto) <= 1400:
            raise ValueError("Escena TTS fuera de límite de caracteres")
        total += len(texto)
    if total > max_caracteres:
        raise ValueError("Límite de caracteres TTS por vídeo alcanzado")
    return len(escenas), total


class NarradorGemini:
    def __init__(self, formato, plan):
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            raise RuntimeError(
                "Para la narración de producción, configura GEMINI_API_KEY"
            )
        self.formato = formato
        self.voz = elegir_voz(formato, plan)
        self.peticiones = 0
        self.max_peticiones = 12 if formato == "short" else 45
        self.segundos = 0.0
        print(
            "NARRACIÓN: Gemini 3.8 Flash TTS | idioma es-ES |",
            "voz:", self.voz, "| contenido:", formato, flush=True
        )

    def narrar(self, texto, ruta):
        if self.peticiones >= self.max_peticiones:
            raise RuntimeError("Máximo de peticiones TTS por vídeo agotado")
        # Una llamada de voz por escena para mantener el audio sincronizado.
        segundos = sintetizar(texto, self.voz, ruta)
        self.peticiones += 1
        self.segundos += segundos
        if self.segundos > (180 if self.formato == "short" else 1200):
            raise RuntimeError("Duración total de narración fuera del límite")
        return segundos
