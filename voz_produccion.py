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
import time
import wave
from pathlib import Path

from voz_gemini_castellano import VOCES, sintetizar, AudioIncompletoError
from voz_azure_castellano import sintetizar as sintetizar_azure, VOCES as VOCES_AZURE

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
    qwen_solicitado = (
        os.environ.get("PF_TTS_PROVIDER", "").strip().lower() == "qwen"
        or (
            not os.environ.get("PF_TTS_PROVIDER", "").strip()
            and config.get("motor_voz") == "qwen3-tts-0.6b"
        )
    )
    voz_config = "Ryan" if qwen_solicitado else mapeo.get(formato, DEFAULT[formato])
    voz = (plan or {}).get("narrador_voz", voz_config)
    if qwen_solicitado:
        if voz != "Ryan":
            raise ValueError("La voz local de Píxel Feroz debe ser Ryan")
    elif voz not in VOCES:
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
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        configurado = config.get("motor_voz", "gemini-3.8-flash-tts")
        solicitado = os.environ.get("PF_TTS_PROVIDER", "").strip().lower()
        if solicitado:
            if solicitado not in ("gemini", "azure"):
                raise ValueError("PF_TTS_PROVIDER debe ser gemini o azure")
            self.proveedor = solicitado
        elif configurado == "azure-neural":
            self.proveedor = "azure"
        else:
            self.proveedor = "gemini"

        if self.proveedor == "gemini":
            if not os.environ.get("GEMINI_API_KEY", "").strip():
                raise RuntimeError(
                    "Para la narración Gemini, configura GEMINI_API_KEY"
                )
        elif not (
            os.environ.get("AZURE_SPEECH_KEY", "").strip()
            and os.environ.get("AZURE_SPEECH_REGION", "").strip()
        ):
            raise RuntimeError(
                "Para Azure, configura AZURE_SPEECH_KEY y "
                "AZURE_SPEECH_REGION en GitHub Secrets"
            )
        self.formato = formato
        self.voz = elegir_voz(formato, plan)
        self.voz_real = (
            VOCES_AZURE["Alvaro" if formato == "short" else "Arnau"]
            if self.proveedor == "azure" else self.voz
        )
        self.peticiones = 0
        self.max_peticiones = 24 if formato == "short" else 90
        self.segundos = 0.0
        # Con Gemini TTS varios fragmentos consecutivos disparaban HTTP 429
        # tras 5 solicitudes en ~60 segundos. Cada bloque largo se inicia
        # como mínimo 35 segundos después del anterior.
        self.intervalo = (35.0 if formato == "largo" else 0.0) if self.proveedor == "gemini" else 4.0
        self.ultimo_inicio = None
        self.recuperados = 0
        print(
            "NARRACIÓN:", self.proveedor,
            "| voz real:", self.voz_real,
            "| idioma es-ES | contenido:", formato, flush=True
        )

    def _limitar_ritmo(self):
        ahora = time.monotonic()
        if self.ultimo_inicio is not None and self.intervalo > 0:
            segundos = self.intervalo - (ahora - self.ultimo_inicio)
            if segundos > 0:
                print(
                    "Narración " + self.voz + ": respetando intervalo "
                    "de peticiones (" + str(round(segundos, 1)) + "s)",
                    flush=True,
                )
                time.sleep(segundos)
        self.ultimo_inicio = time.monotonic()

    @staticmethod
    def _recuperar_wav(ruta, esperado_minimo):
        if not ruta.is_file() or ruta.stat().st_size < 10_000:
            return None
        try:
            with wave.open(str(ruta), "rb") as wav:
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                    return None
                frames = wav.getnframes()
                frecuencia = wav.getframerate()
                segundos = frames / frecuencia if frecuencia > 0 else 0
            if esperado_minimo <= segundos <= 90:
                return segundos
        except (OSError, wave.Error, EOFError, ValueError):
            pass
        return None

    def narrar(self, texto, ruta):
        ruta = Path(ruta)
        if self.peticiones >= self.max_peticiones:
            raise RuntimeError("Máximo de peticiones TTS por vídeo agotado")
        esperado_minimo = max(2.0, len(texto.split()) / 5.0)

        # Checkpoint privado del runner actual, ligado a la huella del guion
        # y narrador por el directorio del motor. Nunca subir al artifacts
        # público ni al repositorio para no filtrar vídeos no publicados.
        recuperado = self._recuperar_wav(ruta, esperado_minimo)
        if recuperado is not None:
            self.recuperados += 1
            self.segundos += recuperado
            print(
                "Reutilizando WAV validado del runner:",
                ruta.name, "|", round(recuperado, 1), "segundos", flush=True,
            )
            if self.segundos > (180 if self.formato == "short" else 1200):
                raise RuntimeError("Duración total de narración fuera del límite")
            return recuperado
        if ruta.is_file():
            ruta.unlink()

        ultimo_error = None
        for intento in range(3):
            if self.peticiones >= self.max_peticiones:
                raise RuntimeError("Máximo de peticiones TTS por vídeo agotado")
            self._limitar_ritmo()
            self.peticiones += 1
            try:
                if self.proveedor == "azure":
                    seleccion = "Alvaro" if self.formato == "short" else "Arnau"
                    segundos = sintetizar_azure(
                        preparar_lectura(texto), seleccion, ruta
                    )
                else:
                    segundos = sintetizar(preparar_lectura(texto), self.voz, ruta)
                if segundos < esperado_minimo:
                    raise AudioIncompletoError(
                        "La duración del audio es insuficiente para el texto"
                    )
                ultimo_error = None
                break
            except AudioIncompletoError as exc:
                ultimo_error = exc
                ruta.unlink(missing_ok=True)
                if intento < 2 and self.peticiones < self.max_peticiones:
                    print(
                        "::warning::El proveedor devolvió un fragmento incompleto. "
                        "Regenerando con " + self.voz
                        + " (" + str(intento + 2) + "/3).",
                        flush=True,
                    )
                else:
                    raise RuntimeError(
                        "Tres intentos de audio incompleto para un fragmento. "
                        "No se subirá el vídeo."
                    ) from None
        if ultimo_error is not None:
            raise RuntimeError("No se pudo completar el fragmento TTS")
        self.segundos += segundos
        if self.segundos > (180 if self.formato == "short" else 1200):
            raise RuntimeError("Duración total de narración fuera del límite")
        return segundos
