#!/usr/bin/env python3
"""Resiliencia para Gemini sin filtrar prompts ni claves en los logs.

429 puede indicar límites por minuto, tokens o día. Se respeta Retry-After,
se espera al menos una ventana de cuota al reintentar un 429, y se distingue
un límite diario comprobado (no sirve reintentarlo cada pocos segundos).
"""
import datetime
import email.utils
import json
import random
import time
import urllib.error
import urllib.request

ESTADOS_TRANSITORIOS = frozenset((429, 500, 502, 503, 504))


class GeminiQuotaError(RuntimeError):
    """La cuota impide continuar temporalmente con esta solicitud."""


class GeminiDailyQuotaError(GeminiQuotaError):
    """El proveedor identifica explícitamente un límite diario."""


def analizar_cuota(exc):
    """Interpretar solo pistas de cuota; nunca exponer el texto del proveedor."""
    if exc.code != 429:
        return "indeterminada"
    try:
        contenido = exc.read(16384).decode("utf-8", errors="replace")
    except (OSError, UnicodeError, ValueError):
        return "indeterminada"
    try:
        datos = json.loads(contenido)
    except (ValueError, TypeError):
        return "indeterminada"

    pistas = []
    if isinstance(datos, dict):
        error = datos.get("error", {})
        if isinstance(error, dict):
            # Hay variantes en Google APIs: quota_limit, quotaLimit,
            # quotaMetric, reason, description y message.
            pistas.append(str(error.get("status", "")))
            pistas.append(str(error.get("message", ""))[:1200])
            for detalle in error.get("details", []):
                if isinstance(detalle, dict):
                    pistas.append(json.dumps(detalle, ensure_ascii=True)[:2500])
    resumen = " ".join(pistas).lower()
    if any(p in resumen for p in (
        "perday", "per_day", "per day", "requestsperday",
        "requests_per_day", "daily quota", "day limit",
    )):
        return "diaria"
    if any(p in resumen for p in (
        "perminute", "per_minute", "per minute", "persecond",
        "per_second", "per second", "ratelimit",
    )):
        return "por_minuto"
    return "indeterminada"


def espera_retry_after(exc):
    valor = (exc.headers.get("Retry-After")
             if getattr(exc, "headers", None) is not None else None)
    if valor is None:
        return None
    try:
        return max(0.0, min(240.0, float(valor)))
    except (TypeError, ValueError):
        try:
            fecha = email.utils.parsedate_to_datetime(valor)
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=datetime.timezone.utc)
            segundos = (fecha - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            return max(0.0, min(240.0, segundos))
        except (TypeError, ValueError, OverflowError):
            return None


def _esperar(contexto, motivo, intento, max_intentos, segundos=None):
    if segundos is None:
        segundos = min(20.0, 2.0 * (2 ** intento))
    demora = segundos + random.uniform(0, 1)
    print(
        f"::warning::{contexto}: {motivo}; "
        f"reintento {intento + 2}/{max_intentos} tras {demora:.1f}s",
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
            codigo = exc.code
            if codigo not in ESTADOS_TRANSITORIOS:
                raise
            if codigo == 429:
                tipo = analizar_cuota(exc)
                exc.close()
                if tipo == "diaria":
                    raise GeminiDailyQuotaError(
                        f"{contexto}: Google indica que se alcanzó la cuota "
                        "diaria. Revisa AI Studio; esperar unos segundos no "
                        "permite continuar."
                    ) from None
                if intento + 1 == max_intentos:
                    raise GeminiQuotaError(
                        f"{contexto}: HTTP 429 persiste tras {max_intentos} "
                        "intentos y esperas largas. Comprobar cuota del "
                        "proyecto en AI Studio."
                    ) from None
                # Si Google no envía una fecha, esperamos una ventana
                # suficiente para la mayoría de límites por minuto.
                pausa = espera_retry_after(exc)
                if pausa is None:
                    pausa = [65, 95, 125, 160][intento]
                _esperar(contexto, "HTTP 429 / cuota",
                         intento, max_intentos, segundos=pausa)
                continue
            if intento + 1 == max_intentos:
                raise
            exc.close()
            _esperar(contexto, f"HTTP {codigo}", intento, max_intentos)
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if intento + 1 == max_intentos:
                raise RuntimeError(
                    f"{contexto}: conexión agotada tras {max_intentos} "
                    "intentos; no se ha completado la solicitud a Gemini."
                ) from None
            _esperar(contexto, "conexión interrumpida o tiempo agotado",
                     intento, max_intentos)
    raise RuntimeError("No se recibió respuesta de Gemini")
