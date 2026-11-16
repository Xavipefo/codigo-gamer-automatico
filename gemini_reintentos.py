#!/usr/bin/env python3
"""Reintentos limitados para peticiones REST a Gemini (texto y audio).

Controla HTTP 429/5xx y desconexiones transitorias, incluidas las
esperas de red agotadas que aparecen en la narración de vídeos largos.
No muestra la clave API, el guion, las respuestas ni los enlaces firmados.
Cada reintento puede consumir cuota; los límites impiden bucles ilimitados.
"""
import json
import random
import time
import urllib.error
import urllib.request

ESTADOS_TRANSITORIOS = frozenset((429, 500, 502, 503, 504))


def _esperar(contexto, motivo, intento, max_intentos):
    demora = min(16.0, 2.0 * (2 ** intento)) + random.uniform(0, 0.8)
    print(
        f"::warning::{contexto}: {motivo}; "
        f"reintento {intento + 2}/{max_intentos} "
        f"tras {demora:.1f}s",
        flush=True,
    )
    time.sleep(demora)


def solicitar_json(request, timeout=110, max_intentos=4, contexto="Gemini"):
    if not 1 <= max_intentos <= 5:
        raise ValueError("Número de intentos fuera de límite")
    if not 10 <= timeout <= 180:
        raise ValueError("Tiempo máximo por intento fuera de límites")
    for intento in range(max_intentos):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as respuesta:
                return json.load(respuesta)
        except urllib.error.HTTPError as exc:
            # HTTPError hereda de URLError: debe tratarse primero.
            if exc.code not in ESTADOS_TRANSITORIOS or intento + 1 == max_intentos:
                raise
            try:
                exc.close()
            finally:
                _esperar(contexto, f"HTTP {exc.code}", intento, max_intentos)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            # No reflejar la URL ni la causa textual: pueden contener
            # datos privados del trabajo. Un error de conexión final hace
            # fallar el vídeo ANTES de cualquier subida a YouTube.
            if intento + 1 == max_intentos:
                raise RuntimeError(
                    f"{contexto}: conexión agotada tras "
                    f"{max_intentos} intentos; no se ha completado "
                    "la solicitud a Gemini."
                ) from None
            _esperar(contexto, "conexión interrumpida o tiempo agotado",
                     intento, max_intentos)
    raise RuntimeError("No se recibió respuesta de Gemini")
