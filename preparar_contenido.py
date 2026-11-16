#!/usr/bin/env python3
"""Prepara guiones revisables de Código Gamer a partir de hechos con fuentes.

No consulta servicios de IA, no descarga material de terceros y no publica.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent
FUENTES = BASE / "temas_verificados.json"
DESTINO = BASE / "salida"
DOMINIOS = ("rockstargames.com", "take2games.com")


def comprobar_enlace(url):
    """Acepta únicamente enlaces HTTPS de fuentes oficiales conocidas."""
    try:
        u = urlparse(url)
        dominio = (u.hostname or "").lower()
        return u.scheme == "https" and any(
            dominio == d or dominio.endswith("." + d) for d in DOMINIOS
        )
    except ValueError:
        return False


def texto_limpio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("Campo de texto obligatorio: " + campo)
    valor = re.sub(r"\s+", " ", valor).strip()
    if len(valor) > 600:
        raise ValueError("Campo demasiado largo: " + campo)
    return valor


def validar_tema(tema):
    if not isinstance(tema, dict):
        raise ValueError("Un tema debe ser un objeto JSON")
    identificador = texto_limpio(tema.get("id"), "id")
    if not re.fullmatch(r"[a-z0-9_-]{3,60}", identificador):
        raise ValueError("ID inválido: " + identificador)
    texto_limpio(tema.get("titulo"), "titulo")
    texto_limpio(tema.get("gancho"), "gancho")
    texto_limpio(tema.get("contexto"), "contexto")
    if tema.get("estado") != "confirmado":
        raise ValueError("Solo se admiten temas confirmados: " + identificador)
    comprobado = date.fromisoformat(tema["fecha_verificacion"])
    if comprobado > date.today():
        raise ValueError("La fecha de verificación no puede ser futura")
    caduca = tema.get("vigente_hasta")
    if caduca and date.fromisoformat(caduca) < date.today():
        raise ValueError("Tema caducado: " + identificador)
    hechos = tema.get("hechos")
    if not isinstance(hechos, list) or len(hechos) < 2:
        raise ValueError("Se necesitan al menos dos hechos: " + identificador)
    for i, hecho in enumerate(hechos, 1):
        texto_limpio(hecho.get("texto"), "hechos[" + str(i) + "].texto")
        url = hecho.get("fuente")
        if not isinstance(url, str) or not comprobar_enlace(url):
            raise ValueError("Fuente oficial HTTPS no válida en hecho " + str(i))
    return tema


def cargar_temas(ruta):
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if not isinstance(datos, list) or not datos:
        raise ValueError("El archivo debe contener una lista no vacía")
    temas = [validar_tema(t) for t in datos]
    ids = [t["id"] for t in temas]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs de temas duplicados")
    return temas


def preparar(tema):
    hechos = [texto_limpio(h["texto"], "texto") for h in tema["hechos"]]
    gancho = texto_limpio(tema["gancho"], "gancho")
    contexto = texto_limpio(tema["contexto"], "contexto")
    frases = [gancho, contexto] + hechos + [
        "Seguiremos las novedades confirmadas, sin confundir rumores con anuncios oficiales."
    ]
    guion = " ".join(frase.rstrip(".!?") + "." for frase in frases)
    referencias = list(dict.fromkeys(h["fuente"] for h in tema["hechos"]))
    descripcion = (
        tema["titulo"] + "\n\n"
        "Un resumen de información confirmada. Revisa siempre las fuentes originales.\n\n"
        + "Fuentes:\n" + "\n".join(referencias)
        + "\n\n#GTAVI #Videojuegos #CodigoGamer\n"
    )
    plan = {
        "canal": "Codigo Gamer",
        "tema_id": tema["id"],
        "titulo_propuesto": tema["titulo"],
        "estado": "BORRADOR_PENDIENTE_REVISION",
        "publicacion_automatica": False,
        "fecha_preparacion": date.today().isoformat(),
        "fecha_verificacion": tema["fecha_verificacion"],
        "duracion_objetivo_segundos": [35, 55],
        "visual": "Gráficos y animaciones originales; no utilizar gameplay ajeno sin permiso",
        "escenas": [
            {"tipo": "gancho", "texto": gancho},
            {"tipo": "contexto", "texto": contexto},
            *[{"tipo": "hecho_verificado", "texto": h["texto"], "fuente": h["fuente"]}
              for h in tema["hechos"]],
            {"tipo": "cierre", "texto": frases[-1]},
        ],
        "fuentes": referencias,
        "revisiones_pendientes": [
            "Comprobar que los enlaces respaldan cada afirmación",
            "Verificar que no haya noticias más recientes",
            "Confirmar la pronunciación y el ritmo de la voz",
            "Revisar derechos de música, imágenes y clips",
            "Revisar título, miniatura, montaje y duración",
        ],
    }
    return guion, descripcion, plan


def main():
    p = argparse.ArgumentParser(description="Genera borradores editoriales para Código Gamer")
    p.add_argument("--tema", help="ID del tema; por defecto, el primero")
    p.add_argument("--fuentes", type=Path, default=FUENTES)
    p.add_argument("--salida", type=Path, default=DESTINO)
    args = p.parse_args()
    temas = cargar_temas(args.fuentes)
    encontrados = [t for t in temas if t["id"] == args.tema] if args.tema else temas[:1]
    if not encontrados:
        p.error("Tema no encontrado")
    tema = encontrados[0]
    guion, descripcion, plan = preparar(tema)
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "guion.txt").write_text(guion + "\n", encoding="utf-8")
    (args.salida / "descripcion.txt").write_text(descripcion, encoding="utf-8")
    (args.salida / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Preparado:", tema["id"])
    print("Palabras:", len(guion.split()))
    print("Estado: BORRADOR_PENDIENTE_REVISION; no se publica ningún vídeo")
    print("Salida:", args.salida.resolve())


if __name__ == "__main__":
    main()
