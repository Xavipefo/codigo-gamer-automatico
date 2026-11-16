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
import re
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


def preparar_lectura(texto):
    """Facilita la pronunciación castellana sin modificar el guion editorial.

    Solo aplica equivalencias comunes y semánticamente idénticas para evitar
    lecturas 'vi' o nombres de letras en inglés. El texto visible se mantiene.
    """
    cambios = (
        (r"\bGTA[\s-]*VI\b", "GTA seis"),
        (r"\bGTA[\s-]*V\b", "GTA cinco"),
        (r"\bPS\s*5\b", "PlayStation cinco"),
        (r"\bPS\s*4\b", "PlayStation cuatro"),
        (r"\b(\d{1,3})\s*FPS\b",
         lambda x: x.group(1) + " fotogramas por segundo"),
        (r"\b(\d{1,3})\s*GB\b",
         lambda x: x.group(1) + " gigabytes"),
    )
    for patron, reemplazo in cambios:
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
    return texto


class NarradorGemini:
    def __init__(self, formato, plan):
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            raise RuntimeError(
                "Para la narración de producción, configura GEMINI_API_KEY"
            )
        self.formato = formato
        self.voz = elegir_voz(formato, plan)
        self.peticiones = 0
        self.max_peticiones = 24 if formato == "short" else 90
        self.segundos = 0.0
        print(
            "NARRACIÓN: Gemini 3.8 Flash TTS | idioma es-ES |",
            "voz:", self.voz, "| contenido:", formato, flush=True
        )

    def narrar(self, texto, ruta):
        if self.peticiones >= self.max_peticiones:
            raise RuntimeError("Máximo de peticiones TTS por vídeo agotado")
        # Cada escena se narra con una sola voz, comprobando que la API no
        # haya devuelto un audio truncado. En la prueba larga anterior,
        # un fragmento terminó en 8.8 s tras narrar muchas más palabras.
        esperado_minimo = max(2.0, len(texto.split()) / 5.0)
        for intento in range(2):
            segundos = sintetizar(preparar_lectura(texto), self.voz, ruta)
            self.peticiones += 1
            if segundos >= esperado_minimo:
                break
            if intento == 0 and self.peticiones < self.max_peticiones:
                print(
                    "::warning::Audio aparentemente incompleto: "
                    "regenerando el fragmento con la misma voz.",
                    flush=True,
                )
            else:
                raise RuntimeError(
                    "La voz devolvió una narración demasiado corta para "
                    "el guion. No se subirá el vídeo incompleto."
                )
        self.segundos += segundos
        if self.segundos > (180 if self.formato == "short" else 1200):
            raise RuntimeError("Duración total de narración fuera del límite")
        return segundos
