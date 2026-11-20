#!/usr/bin/env python3
"""Prepara guiones revisables de Píxel Feroz a partir de hechos con fuentes.

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
DOMINIOS = (
    "rockstargames.com", "take2games.com", "blog.playstation.com",
    "news.xbox.com", "nintendo.com", "ea.com", "ubisoft.com",
    "store.steampowered.com", "bethesda.net",
)


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
    miniatura = tema.get("texto_miniatura")
    if miniatura is not None and (not isinstance(miniatura, str)
                                 or not 1 <= len(miniatura.strip()) <= 90):
        raise ValueError("Texto de miniatura no válido")
    if tema.get("descripcion_personalizada") is not None:
        texto_limpio(tema["descripcion_personalizada"], "descripcion_personalizada")
    formatos = tema.get("formatos", ["short"])
    if not isinstance(formatos, list) or not formatos or any(
        valor not in ("short", "largo") for valor in formatos
    ):
        raise ValueError("Formatos de tema no válidos")
    if "largo" in formatos:
        esquema = tema.get("esquema_largo", [])
        manual = tema.get("escenas_largas", [])
        if isinstance(esquema, list) and any(
            not isinstance(x, str) or not x.strip() or len(x) > 200
            for x in esquema
        ):
            raise ValueError("Esquema del largo inválido")
        if not (isinstance(esquema, list) and len(esquema) >= 6) and not (
            isinstance(manual, list) and len(manual) >= 8
        ):
            raise ValueError("Tema largo sin esquema_largo o escenas_largas")
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
    ids = [t.get("id") for t in datos if isinstance(t, dict)]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs de temas duplicados")
    temas = []
    for tema in datos:
        if not isinstance(tema, dict):
            raise ValueError("Cada tema debe ser un objeto JSON")
        vence = tema.get("vigente_hasta")
        if vence and date.fromisoformat(vence) < date.today():
            continue
        temas.append(validar_tema(tema))
    if not temas:
        raise ValueError("No quedan temas vigentes: añadir fuentes nuevas")
    return temas


CTA_SUSCRIPCION = "Suscríbete a Píxel Feroz."
MAX_PALABRAS_SHORT = 88
DESCRIPCION_COMUN = BASE / "descripcion_general.txt"


def construir_descripcion(tema, formato):
    """Descripción específica con hechos y fuentes, seguida de la sección fija."""
    introduccion = (tema.get("descripcion_personalizada")
                    or tema["contexto"]).strip()
    hechos = [h["texto"].strip() for h in tema["hechos"]]
    referencias = list(dict.fromkeys(h["fuente"] for h in tema["hechos"]))
    general = DESCRIPCION_COMUN.read_text(encoding="utf-8").strip()
    # La atribución no sustituye licencias: solo fuentes autorizadas.
    from visuales_autorizados import creditos_para_descripcion
    from video_material import creditos_clips
    creditos_imagenes = creditos_para_descripcion(tema["id"])
    creditos_video = creditos_clips(tema["id"])
    bloque_creditos = (
        "\n\nIMÁGENES CON DERECHOS CONFIRMADOS:\n"
        + "\n".join(creditos_imagenes)
    ) if creditos_imagenes else ""
    if creditos_video:
        bloque_creditos += (
            "\n\nCLIPS UTILIZADOS CON DERECHOS CONFIRMADOS:\n"
            + "\n".join(creditos_video)
        )
    etiqueta = "#GTAVI " if "gta" in tema["id"].lower() else ""
    bloque = (
        f"{tema['titulo']}\n\n"
        f"{introduccion}\n\n"
        "EN ESTE VÍDEO:\n"
        + "\n".join("• " + h for h in hechos)
        + "\n\nFUENTES OFICIALES:\n"
        + "\n".join(referencias)
        + bloque_creditos
        + f"\n\n{etiqueta}{'#Shorts ' if formato == 'short' else ''}#PixelFeroz\n"
        + "\n------------------------------\n\n"
        + general
        + "\n"
    )
    if len(bloque) > 4900:
        raise ValueError("Descripción demasiado larga para YouTube")
    return bloque


def preparar(tema):
    # Los Shorts solo narran las primeras tres afirmaciones: los restantes
    # sirven para la investigación de formatos largos y la descripción.
    hechos = [texto_limpio(h["texto"], "texto")
              for h in tema["hechos"][:3]]
    gancho = texto_limpio(tema["gancho"], "gancho")
    contexto = texto_limpio(tema["contexto"], "contexto")
    # PF-41: un Short es una noticia concreta, no una recapitulación
    # exhaustiva. Los hechos omitidos siguen disponibles, íntegros y con
    # sus fuentes en la descripción, sin recortar frases a mitad.
    cierre = CTA_SUSCRIPCION
    seleccion = [
        {"tipo": "gancho", "texto": gancho},
        *[
            {
                "tipo": "hecho_verificado",
                "texto": x,
                "fuente": tema["hechos"][i]["fuente"]
            }
            for i, x in enumerate(hechos[:2])
        ],
    ]
    base_palabras = sum(len(x["texto"].split()) for x in seleccion)
    margen = MAX_PALABRAS_SHORT - base_palabras - len(cierre.split())
    if len(contexto.split()) <= margen and contexto not in (gancho, *hechos):
        seleccion.insert(1, {"tipo": "contexto", "texto": contexto})
        margen -= len(contexto.split())
    if len(hechos) > 2 and len(hechos[2].split()) <= margen:
        seleccion.append({
            "tipo": "hecho_verificado",
            "texto": hechos[2],
            "fuente": tema["hechos"][2]["fuente"],
        })
    seleccion.append({"tipo": "cierre", "texto": cierre})
    guion = " ".join(x["texto"] for x in seleccion)
    referencias = list(dict.fromkeys(h["fuente"] for h in tema["hechos"]))
    descripcion = construir_descripcion(tema, "short")
    plan = {
        "canal": "Píxel Feroz",
        "tema_id": tema["id"],
        "titulo_propuesto": tema["titulo"],
        "texto_miniatura": tema.get("texto_miniatura", tema["titulo"])[:90],
        "etiquetas": [
            "videojuegos", "gaming", "Píxel Feroz",
            *(["GTA VI"] if "gta" in tema["id"].lower() else []),
        ],
        "estado": "BORRADOR_PENDIENTE_REVISION",
        "publicacion_automatica": False,
        "fecha_preparacion": date.today().isoformat(),
        "fecha_verificacion": tema["fecha_verificacion"],
        "duracion_objetivo_segundos": [25, 42],
        "estilo_retencion": "PF-41-ganchos-directos-planos-3s",
        "visual": "Gráficos originales; no usar gameplay ajeno sin permiso",
        "escenas": seleccion,
        "fuentes": referencias,
        "revisiones_pendientes": [
            "Comprobar que las fuentes respaldan cada afirmación",
            "Verificar que no haya noticias posteriores",
            "Revisar narración, derechos visuales y montaje",
            "Comprobar miniatura, título y descripción personalizada",
        ],
    }
    return guion, descripcion, plan


def main():
    p = argparse.ArgumentParser(description="Genera borradores editoriales para Píxel Feroz")
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
