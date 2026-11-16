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

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
TEMAS = BASE / "temas_verificados.json"
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODELO_DEFAULT = "gemini-2.5-flash-lite"


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


def solicitar(prompt, api_key):
    modelo = os.environ.get("GEMINI_MODEL", MODELO_DEFAULT).strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", modelo):
        raise ValueError("Nombre de modelo GEMINI_MODEL inválido")
    data = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 7500,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        URL.format(model=modelo),
        data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=110) as respuesta:
            resultado = json.load(respuesta)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            "Gemini devolvió HTTP " + str(exc.code)
            + ". Revisa el secreto, el modelo y la cuota del proyecto."
        ) from None
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "No se pudo conectar con Gemini: " + type(exc.reason).__name__
        ) from None
    try:
        partes = resultado["candidates"][0]["content"]["parts"]
        texto = "".join(p.get("text", "") for p in partes).strip()
        data = json.loads(texto)
        return data["escenas"]
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        raise ValueError("Gemini no devolvió un JSON de escenas válido") from exc


def construir_prompt(tema, formato):
    lista_hechos = "\n".join(
        "- " + h["texto"] + "\n  FUENTE: " + h["fuente"]
        for h in tema["hechos"]
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
        " Redacta 8 a 11 escenas narrativas, de 125 a 165 palabras "
        "por escena; total 1150 a 1750 palabras. "
        "Estructura: gran pregunta inicial, contexto, desarrollo por "
        "temas, delimitación de lo desconocido y conclusión con "
        "la llamada a suscribirse. Si la información oficial es "
        "insuficiente, NO rellenes el texto inventando ni repitiendo "
        "datos: devuelve escenas vacías para abortar la producción.\n"
        'Devuelve SOLO JSON: {"escenas":["texto escena 1", ...]}.\n'
    )


def normalizar_escenas(datos, tema, formato):
    if not isinstance(datos, list) or not all(
        isinstance(x, str) and x.strip() for x in datos
    ):
        raise ValueError("Escenas no válidas")
    minesc, maxesc = (5, 7) if formato == "short" else (8, 11)
    if not minesc <= len(datos) <= maxesc:
        raise ValueError("Número de escenas narradas fuera de rango")
    escenas = [texto_plano(s) for s in datos]
    todo = " ".join(escenas)
    # Añadimos la CTA exactamente una vez al final, incluso si el modelo
    # la omitió o la escribió alterada. La versión exacta es la aprobada.
    if CTA_SUSCRIPCION not in escenas[-1]:
        if CTA_SUSCRIPCION in todo:
            escenas = [s.replace(CTA_SUSCRIPCION, "").strip() for s in escenas]
        escenas[-1] = (escenas[-1] + " " + CTA_SUSCRIPCION).strip()
    todo = " ".join(escenas)
    palabras = len(todo.split())
    limites = (70, 125) if formato == "short" else (1100, 1900)
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
    if len(todo) > 12000:
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
