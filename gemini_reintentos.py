#!/usr/bin/env python3
"""Reintentos conservadores para solicitudes REST de Gemini.

Google recomienda espera exponencial para errores 503 y respuestas transitorias.
Se reutiliza exactamente el mismo request, sin cambiar el modelo ni el coste
potencial del trabajo. Los mensajes no contienen claves ni el texto del guion.
"""
import json
import random
import time
import urllib.error
import urllib.request

ESTADOS_TRANSITORIOS = frozenset((429, 500, 502, 503, 504))


def solicitar_json(request, timeout=110, max_intentos=4, contexto="Gemini"):
    if not 1 <= max_intentos <= 5:
        raise ValueError("Número de intentos fuera de límite")
    for intento in range(max_intentos):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as respuesta:
                return json.load(respuesta)
        except urllib.error.HTTPError as exc:
            # Los errores de autenticación, validación y permisos no se
            # reintentan. Tampoco reproducimos el cuerpo de respuesta.
            if exc.code not in ESTADOS_TRANSITORIOS or intento + 1 == max_intentos:
                raise
            demora = min(16.0, 2.0 * (2 ** intento)) + random.uniform(0, 0.8)
            print(
                f"::warning::{contexto}: HTTP {exc.code}, "
                f"reintento {intento + 2}/{max_intentos} "
                f"tras {demora:.1f}s",
                flush=True,
            )
            exc.close()
            time.sleep(demora)
    raise RuntimeError("No se recibió respuesta de Gemini")
