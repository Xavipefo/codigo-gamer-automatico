#!/usr/bin/env python3
"""Tres títulos y tres miniaturas originales para revisión en YouTube Studio.

NO accede a YouTube, NO inicia experimentos ni cambia un vídeo existente.
Los vídeos privados y Shorts NO admiten la herramienta A/B de YouTube.
Diseños creados con Pillow de datos oficiales verificados, sin usar logos
de Rockstar, gameplay, capturas de terceros ni imágenes IA no autorizadas.
"""
import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

from generar_short import fuente, partir_lineas

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
TEMAS = BASE / "temas_verificados.json"

PALETAS = [
    ((6, 18, 36), (42, 223, 215), (245, 251, 252)),
    ((25, 13, 43), (255, 91, 160), (252, 247, 254)),
    ((13, 23, 38), (250, 195, 74), (250, 251, 246)),
]
SUBTITULOS = ("LOS HECHOS", "LAS CLAVES", "ANÁLISIS")


def titulo_corto(texto):
    return re.sub(r"\s+", " ", texto).strip(" .!?")[:100].rstrip(" ,;:")


def titulos_originales(plan, tema):
    oficiales = tema.get("titulos_experimento")
    if oficiales is not None:
        if (not isinstance(oficiales, list) or len(oficiales) != 3
                or not all(isinstance(x, str) for x in oficiales)):
            raise ValueError("Se necesitan exactamente tres títulos alternativos")
        propuestos = [titulo_corto(x) for x in oficiales]
    else:
        base = titulo_corto(plan["titulo_propuesto"])
        propuesta = titulo_corto("GTA VI explicado: " + tema["texto_miniatura"])
        gancho = titulo_corto(tema["gancho"])
        propuestos = [base, propuesta, gancho]
        if len(set(x.casefold() for x in propuestos)) != 3:
            propuestos = [
                base,
                titulo_corto("GTA VI: datos confirmados por Rockstar"),
                titulo_corto("GTA VI: análisis de la información oficial"),
            ]
    if any(not 8 <= len(x) <= 100 for x in propuestos):
        raise ValueError("Título A/B fuera de los límites de YouTube")
    if len({x.casefold() for x in propuestos}) != 3:
        raise ValueError("Los tres títulos A/B deben ser distintos")
    return propuestos


def _fondo(imagen, variante, colores):
    w, h = imagen.size
    d = ImageDraw.Draw(imagen)
    base, acento, blanco = colores
    d.rectangle((0, 0, w, h), fill=base)
    if variante == 0:
        for k in range(18):
            paso = int(k * (w / 15))
            d.polygon(
                [(paso, 0), (paso + int(w * .17), 0),
                 (paso - int(w * .06), h), (paso - int(w * .23), h)],
                fill=tuple(min(255, x + 5 * (k % 3)) for x in base),
            )
        d.rounded_rectangle((38, 38, w-38, h-38), radius=24, outline=acento, width=7)
    elif variante == 1:
        d.ellipse((int(w*.53), -int(h*.45), int(w*1.23), int(h*.95)),
                  outline=acento, width=18)
        d.ellipse((int(w*.58), -int(h*.35), int(w*1.15), int(h*.80)),
                  outline=acento, width=5)
        d.rectangle((0, int(h*.88), w, h), fill=acento)
    else:
        for n in range(7):
            left = int(w*.13*n)
            d.polygon(
                [(left, 0), (left + int(w*.045), 0),
                 (left + int(w*.32), h), (left+int(w*.27), h)],
                fill=tuple(min(255, x+14) for x in base),
            )
        d.rounded_rectangle((int(w*.055), int(h*.06),
                             int(w*.945), int(h*.94)),
                            radius=18, outline=acento, width=4)


def crear_portada(texto, variante, formato, destino):
    w, h = (1280, 720) if formato == "largo" else (720, 1280)
    imagen = Image.new("RGB", (w, h))
    colores = PALETAS[variante]
    _fondo(imagen, variante, colores)
    d = ImageDraw.Draw(imagen)
    _, acento, blanco = colores
    d.text((int(w*.09), int(h*.12)), "PÍXEL FEROZ",
           font=fuente(37 if formato == "largo" else 29, True), fill=acento)
    d.text((int(w*.09), int(h*.22)), "GTA VI",
           font=fuente(74 if formato == "largo" else 60, True), fill=blanco)
    original = titulo_corto(texto).upper()
    ancho = int(w*.77)
    max_lineas = 3 if formato == "largo" else 5
    for tam in range(68 if formato == "largo" else 54, 27, -2):
        f = fuente(tam, True)
        lineas = partir_lineas(d, original, f, ancho)
        if len(lineas) <= max_lineas:
            break
    linea = int(tam * 1.26)
    y = int(h*.40)
    for una in lineas:
        if y + linea >= int(h*.86):
            break
        d.text((int(w*.09), y), una, font=f, fill=blanco)
        y += linea
    d.text((int(w*.09), int(h*.86)),
           SUBTITULOS[variante],
           font=fuente(25 if formato == "largo" else 28, True), fill=acento)
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(destino, format="JPEG", quality=88, optimize=True)
    if destino.stat().st_size > 2_000_000:
        raise RuntimeError("Miniatura A/B supera 2 MB")
    return destino


def generar(plan, tema, directorio):
    formato = plan["formato"]
    alternativas = titulos_originales(plan, tema)
    directorio.mkdir(parents=True, exist_ok=True)
    etiquetas = ("a", "b", "c")
    for i, letra in enumerate(etiquetas):
        rotulo = tema.get("texto_miniatura", plan["titulo_propuesto"])
        if i == 1:
            rotulo = "CLAVES DE " + tema["titulo"].replace("GTA VI:", "").strip()
        elif i == 2:
            rotulo = tema["titulo"]
        crear_portada(rotulo, i, formato, directorio / f"miniatura_{letra}.jpg")
    datos = {
        "tema_id": plan["tema_id"],
        "formato": formato,
        "variantes": [
            {"opcion": k.upper(), "titulo": t, "miniatura": f"miniatura_{k}.jpg"}
            for k,t in zip(etiquetas, alternativas)
        ],
        "estado": "REVISAR_MANUALMENTE",
        "experimentacion_automatica": False,
        "nota": (
            "Los videos largos deben dejar de estar privados antes de iniciar "
            "el A/B en YouTube Studio (solo ordenador y canales elegibles). "
            "Los Shorts no admiten pruebas A/B oficiales."
        ),
        "privacidad_de_artifact": (
            "Si este paquete se descarga como artifact de un repositorio "
            "público, sus miniaturas y títulos pueden ser visibles."
        ),
    }
    (directorio / "experimento.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return datos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=SALIDA / "plan.json")
    parser.add_argument("--salida", type=Path, default=SALIDA / "experimento")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    temas = json.loads(TEMAS.read_text(encoding="utf-8"))
    tema = next((x for x in temas if x["id"] == plan["tema_id"]), None)
    if tema is None or tema["estado"] != "confirmado":
        raise ValueError("No se generan portadas de temas no confirmados")
    res = generar(plan, tema, args.salida)
    print("Paquete de tres títulos y tres portadas preparado:", res["tema_id"])
    print("La prueba A/B debe iniciarse MANUALMENTE en YouTube Studio.")


if __name__ == "__main__":
    main()
