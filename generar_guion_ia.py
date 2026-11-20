#!/usr/bin/env python3
"""Escribe guiones con Gemini únicamente desde datos verificados.

Sin GEMINI_API_KEY, el Short conserva su guion determinista. Para largos con
esquema editorial es obligatorio tener una clave de Gemini en GitHub Secrets.
La salida siempre queda como borrador y solo puede subirse PRIVADA.
"""
import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from preparar_contenido import CTA_SUSCRIPCION
from gemini_reintentos import solicitar_json

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
TEMAS = BASE / "temas_verificados.json"
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELO_DEFAULT = "gemini-3.5-flash-lite"


def texto_plano(valor):
    return re.sub(r"\s+", " ", valor).strip()


def hechos_permitidos(tema):
    return " ".join(
        [tema["titulo"], tema["gancho"], tema["contexto"]]
        + [h["texto"] for h in tema["hechos"]]
    )


def cifras(texto):
    """Evita incorporar cantidades y fechas que no estén en las fuentes."""
    return set(re.findall(r"(?<![A-Za-z0-9])\d+(?:[.,]\d+)?(?![A-Za-z0-9])",
                          texto))


def modelos_fallback():
    """Modelos de generación de texto publicados, nunca modelos de TTS.

    Una variable GEMINI_MODEL explícita tiene prioridad, y se mantienen
    dos opciones conservadoras para evitar un 503 persistente de la primera.
    No se alteran ni el prompt ni las restricciones factuales.
    """
    preferido = os.environ.get("GEMINI_MODEL", MODELO_DEFAULT).strip()
    candidatos = [preferido, "gemini-3.1-flash-lite", "gemini-3.5-flash"]
    resultado = []
    for modelo in candidatos:
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", modelo):
            raise ValueError("Nombre de modelo GEMINI_MODEL inválido")
        if modelo not in resultado:
            resultado.append(modelo)
    return resultado


def solicitar(prompt, api_key):
    modelos = modelos_fallback()
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 7500,
            "responseMimeType": "application/json",
        },
    }
    resultado = None
    ultimo_error = None
    for indice, modelo in enumerate(modelos):
        req = urllib.request.Request(
            URL.format(model=modelo),
            data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            resultado = solicitar_json(
                req, timeout=105,
                max_intentos=(3 if indice == 0 else 2),
                contexto="Guion IA de Píxel Feroz"
            )
            print("Modelo de guion operativo:", modelo, flush=True)
            break
        except urllib.error.HTTPError as exc:
            ultimo_error = exc.code
            # El 503 señala falta de capacidad, mientras que 404 indica
            # que el modelo no está disponible para esta clave. Solo
            # en esos casos se prueba otro modelo permitido.
            if exc.code not in (404, 500, 502, 503, 504):
                raise RuntimeError(
                    "Gemini devolvió HTTP " + str(exc.code)
                    + ". Revisa el acceso y la cuota de la clave."
                ) from None
            if indice + 1 < len(modelos):
                print("::warning::Modelo " + modelo + " no disponible (HTTP "
                      + str(exc.code) + "); probando una alternativa.",
                      flush=True)
        except RuntimeError as exc:
            # Solo los fallos transitorios de conexión permiten cambiar
            # a la siguiente alternativa sin ocultar errores de contenido.
            if "conexión agotada" not in str(exc):
                raise
            ultimo_error = "conexion"
            if indice + 1 < len(modelos):
                print("::warning::La conexión con " + modelo
                      + " se agotó; intentando modelo alternativo.",
                      flush=True)
    if resultado is None:
        raise RuntimeError(
            "No se pudo generar el guion tras probar los modelos "
            "configurados (último error " + str(ultimo_error)
            + "). No se ha creado ni subido ningún vídeo."
        )
    try:
        partes = resultado["candidates"][0]["content"]["parts"]
        texto = "".join(p.get("text", "") for p in partes).strip()
        data = json.loads(texto)
        return data["escenas"]
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        raise ValueError("Gemini no devolvió un JSON de escenas válido") from exc


def construir_prompt(tema, formato):
    hechos = tema["hechos"][:3] if formato == "short" else tema["hechos"]
    lista_hechos = "\n".join(
        "- " + h["texto"] + "\n  FUENTE: " + h["fuente"]
        for h in hechos
    )
    base = (
        "Eres guionista de Píxel Feroz, canal en español sobre videojuegos.\n"
        "Escribe un GUION ORIGINAL, cercano y con alta retención.\n"
        "Los siguientes son LOS ÚNICOS HECHOS confirmados disponibles.\n"
        "No inventes noticias, personajes, características, fechas, cifras,"
        " precios, requisitos ni declaraciones. No presentes especulaciones"
        " como confirmaciones. Puedes hacer preguntas, comparaciones"
        " conceptuales y explicar qué NO está confirmado, sin afirmar"
        " detalles no documentados. No añadas números nuevos.\n"
        "No repitas frases para aumentar la duración.\n"
        "El texto de las escenas es narración lista para locutar; sin"
        " títulos, etiquetas, emojis, numeración ni notas entre corchetes.\n"
        "Incluye al FINAL exactamente esta llamada a la acción:\n"
        + CTA_SUSCRIPCION + "\n\n"
        + "TEMA: " + tema["titulo"] + "\n"
        + "GANCHO ORIENTATIVO: " + tema["gancho"] + "\n"
        + "CONTEXTO: " + tema["contexto"] + "\n"
        + "HECHOS VERIFICADOS:\n" + lista_hechos + "\n"
    )
    if formato == "short":
        return (
            base
            + "\nProduce un Short de 75 a 115 palabras. Divide la narración "
            "en 5 a 7 escenas breves. Empieza con un gancho que genere "
            "curiosidad, desarrolla los hechos y termina con la suscripción.\n"
            'Devuelve SOLO JSON: {"escenas":["texto escena 1", ...]}.\n'
        )
    esquema = tema.get("esquema_largo") or []
    if len(esquema) < 6:
        raise ValueError("Falta esquema_largo con al menos seis capítulos")
    return (
        base
        + "\nESQUEMA EDITORIAL (ideas para organizar lo confirmado, "
        "no nuevas afirmaciones):\n"
        + "\n".join("- " + t for t in esquema)
        + "\nProducción larga de alrededor de 10 a 13 minutos de voz."
        " Redacta 9 a 11 escenas narrativas, de 140 a 170 palabras "
        "por escena; total 1250 a 1850 palabras. "
        "Estructura: gran pregunta inicial, contexto, desarrollo por "
        "temas, delimitación de lo desconocido y conclusión con "
        "la llamada a suscribirse. Si la información oficial es "
        "insuficiente, NO rellenes el texto inventando ni repitiendo "
        "datos: devuelve escenas vacías para abortar la producción.\n"
        'Devuelve SOLO JSON: {"escenas":["texto escena 1", ...]}.\n'
    )


def repartir_escenas_largas(escenas, objetivo=9):
    """Reorganiza pausas sin alterar, inventar ni resumir el guion de Gemini.

    Las respuestas de Gemini pueden traer 8 o 12 escenas aunque tengan una
    narración suficiente. Redistribuimos el texto conservando el orden de las
    palabras. No modifica hechos, cifras ni contenido: solo dónde cortar.
    """
    if not 4 <= len(escenas) <= 18:
        raise ValueError("Gemini entregó una estructura de escenas irreparable")
    fragmentos = []
    for escena in escenas:
        fragmentos.extend(
            parte for parte in re.split(r"(?<=[.!?])\s+", escena)
            if parte.strip()
        )
    while len(fragmentos) < objetivo:
        indice = max(range(len(fragmentos)),
                     key=lambda n: len(fragmentos[n].split()))
        palabras = fragmentos[indice].split()
        if len(palabras) < 24:
            raise ValueError("No se pueden dividir escenas demasiado breves")
        punto = len(palabras) // 2
        fragmentos[indice:indice+1] = [
            " ".join(palabras[:punto]), " ".join(palabras[punto:])
        ]
    grupos = []
    pos = 0
    for numero in range(objetivo):
        pendientes = objetivo - numero
        if pendientes == 1:
            grupos.append(" ".join(fragmentos[pos:]))
            break
        max_fin = len(fragmentos) - (pendientes - 1)
        palabras_restantes = sum(len(s.split()) for s in fragmentos[pos:])
        meta = palabras_restantes / pendientes
        acumulado = 0
        mejor_fin = pos + 1
        error = float("inf")
        for fin in range(pos+1, max_fin+1):
            acumulado += len(fragmentos[fin-1].split())
            distancia = abs(acumulado - meta)
            if distancia < error:
                mejor_fin, error = fin, distancia
        grupos.append(" ".join(fragmentos[pos:mejor_fin]))
        pos = mejor_fin
    if len(grupos) != objetivo or any(not g.strip() for g in grupos):
        raise ValueError("No se pudo reorganizar el guion largo")
    return grupos


def normalizar_escenas(datos, tema, formato):
    if not isinstance(datos, list) or not all(
        isinstance(x, str) and x.strip() for x in datos
    ):
        raise ValueError("Escenas no válidas")
    escenas = [texto_plano(s) for s in datos]
    if formato == "short":
        if not 5 <= len(escenas) <= 7:
            raise ValueError("Número de escenas narradas fuera de rango")
    else:
        # Gemini a menudo devuelve 8 o 12 escenas con texto válido. No
        # descartamos una narración íntegra solo por sus límites de escena.
        if not 9 <= len(escenas) <= 11:
            escenas = repartir_escenas_largas(escenas)
    # La CTA aprobada va al final y se presenta exactamente una vez.
    escenas = [s.replace(CTA_SUSCRIPCION, "").strip() for s in escenas]
    # Es perfectamente válido que Gemini dedique la última escena SOLO a
    # la CTA solicitada. Tras quitar duplicados, esa última escena queda
    # vacía: debemos restaurar la CTA, no rechazar todo el guion.
    # Una escena vacía en otra posición sigue siendo un error real.
    if any(not s for s in escenas[:-1]):
        raise ValueError("Gemini devolvió una escena vacía")
    escenas[-1] = (escenas[-1] + " " + CTA_SUSCRIPCION).strip()
    todo = " ".join(escenas)
    palabras = len(todo.split())
    # Un guion de 1053 palabras ya supera ampliamente un Short. Evitamos
    # repetir una generación completa por desviarse un ~4% del mínimo
    # anterior, manteniendo el límite superior y todas las comprobaciones.
    limites = (70, 125) if formato == "short" else (1000, 1900)
    if not limites[0] <= palabras <= limites[1]:
        raise ValueError(
            f"Guion de {palabras} palabras fuera de {limites}"
        )
    no_permitidas = cifras(todo) - cifras(hechos_permitidos(tema))
    if no_permitidas:
        raise ValueError(
            "El guion contiene cifras no verificadas: "
            + ", ".join(sorted(no_permitidas))
        )
    if len(todo) > 19000:
        raise ValueError("El guion supera el límite razonable de caracteres")
    tipos = []
    for i, escena in enumerate(escenas):
        tipo = "gancho" if i == 0 else "cierre" if i == len(escenas)-1 else (
            "contexto" if i == 1 else "hecho_verificado"
        )
        tipos.append({"tipo": tipo, "texto": escena})
    return tipos, todo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formato", choices=("short", "largo"), required=True)
    args = parser.parse_args()
    plan_file = SALIDA / "plan.json"
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    if plan.get("formato") != args.formato:
        raise ValueError("El formato de la IA no coincide con el plan")
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave and args.formato == "short":
        print("Sin GEMINI_API_KEY: Short verificable con guion estructurado.")
        return
    if not clave and plan.get("requiere_guion_ia"):
        raise RuntimeError(
            "Para generar vídeos largos automáticamente, configura "
            "GEMINI_API_KEY en los GitHub Actions Secrets de este repositorio."
        )
    if not plan.get("requiere_guion_ia") and args.formato == "largo":
        print("Guion largo editorial ya disponible; no se invoca la IA.")
        return
    temas = json.loads(TEMAS.read_text(encoding="utf-8"))
    tema = next(
        (t for t in temas if t.get("id") == plan.get("tema_id")), None
    )
    if tema is None or tema.get("estado") != "confirmado":
        raise ValueError("El tema de IA debe estar confirmado en la cola")
    prompt = construir_prompt(tema, args.formato)
    escenas = None
    texto = None
    for intento in range(2):
        try:
            respuesta = solicitar(prompt, clave)
            escenas, texto = normalizar_escenas(respuesta, tema, args.formato)
            break
        except ValueError as exc:
            print(
                "Guion no apto, intento", intento+1,
                "-", str(exc)[:150], flush=True
            )
            if intento == 1:
                if args.formato == "short":
                    # Ya se preparó un guion local con hechos y enlaces
                    # verificados en editorial.py. Evitar que una salida
                    # defectuosa de Gemini bloquee los demás Shorts del lote.
                    # No se añaden afirmaciones ni cifras de la IA fallida.
                    print(
                        "::warning::Gemini no produjo un Short válido tras "
                        "dos intentos; se conserva el guion editorial "
                        "verificado y se aplicará el control de calidad.",
                        flush=True,
                    )
                    return
                raise
    plan["escenas"] = escenas
    plan["huella_guion"] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    plan["requiere_guion_ia"] = False
    plan["origen_guion"] = "gemini_revisable"
    plan_file.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (SALIDA / "guion.txt").write_text(texto + "\n", encoding="utf-8")
    print(
        "Guion IA generado:", plan["tema_id"],
        "| escenas:", len(escenas),
        "| palabras:", len(texto.split()),
        "| solo subida privada", flush=True
    )


if __name__ == "__main__":
    main()
