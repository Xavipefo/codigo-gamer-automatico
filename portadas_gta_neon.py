#!/usr/bin/env python3
"""Portadas llamativas de GTA VI con capturas oficiales del banco verificado.

Solo utiliza ficheros locales validados por rockstar_media.py; no extrae fotos
de redes sociales ni inventa fotogramas. Sin banco, usa fondo geométrico,
sin fingir que es una captura del juego. No publica nada en YouTube.
"""
import hashlib
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from generar_short import fuente as fuente_dejavu
from rockstar_media import BASE as BANCO_ROCKSTAR

PALETAS = {
    "fucsia": {"neon": (255, 38, 149), "secondary": (255, 226, 55), "ink": (15, 7, 43)},
    "amarillo": {"neon": (255, 231, 48), "secondary": (255, 68, 96), "ink": (18, 10, 36)},
    "cian": {"neon": (0, 247, 239), "secondary": (255, 69, 166), "ink": (5, 14, 44)},
    "violeta": {"neon": (177, 84, 255), "secondary": (0, 248, 245), "ink": (12, 6, 43)},
}
TEMAS_PERMITIDOS = ("vice", "leonida", "duo", "jason", "lucia", "cal",
                    "brian", "boobie", "drequan", "real", "raul",
                    "grassrivers", "port", "ambrosia", "kalaga",
                    "artwork", "ultimate", "vintage")


def titular_breve(texto):
    """No deja un bloque de prosa encima de la fotografía."""
    limpio = re.sub(r"\s+", " ", str(texto)).strip(" !")
    palabras = limpio.split()
    if not palabras:
        return "GTA VI"
    return " ".join(palabras[:5]).upper()


def elegir_foto(plan, banco=BANCO_ROCKSTAR):
    """Selecciona por categoría comprobable, no por nombre inventado."""
    banco = Path(banco)
    indice = banco / "catalogo.json"
    if not indice.is_file():
        return None
    try:
        datos = json.loads(indice.read_text(encoding="utf-8"))
        if datos.get("origen") != "https://www.rockstargames.com/VI/media/screenshots":
            return None
        preferidos = [x for x in
                      [plan.get("portada_categoria")] + plan.get("visuales_preferidos", [])
                      if x in TEMAS_PERMITIDOS]
        preferidos += ["artwork", "vice", "duo"]
        disponibles = []
        for elemento in datos.get("imagenes", []):
            destino = (banco / elemento["archivo"]).resolve()
            if not destino.is_relative_to(banco.resolve()) or not destino.is_file():
                continue
            disponibles.append((elemento.get("categoria"), destino))
        for categoria in preferidos:
            candidatas = [p for tipo, p in disponibles if tipo == categoria]
            if candidatas:
                # Estabilidad: la misma portada mantiene la misma imagen al regenerar.
                clave = str(plan.get("tema_id", "")) + categoria
                pos = int(hashlib.sha256(clave.encode()).hexdigest()[:8], 16) % len(candidatas)
                return sorted(candidatas)[pos]
        return disponibles[0][1] if disponibles else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def ajustar_fuente(draw, texto, ancho, max_lineas, inicio):
    palabras = texto.split()
    for tam in range(inicio, 25, -3):
        f = fuente_dejavu(tam, True)
        lineas, actual = [], ""
        for palabra in palabras:
            frase = (actual + " " + palabra).strip()
            if draw.textbbox((0, 0), frase, font=f, stroke_width=2)[2] <= ancho:
                actual = frase
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)
        if len(lineas) <= max_lineas and all(
            draw.textbbox((0, 0), linea, font=f, stroke_width=2)[2] <= ancho
            for linea in lineas
        ):
            return f, lineas
    raise ValueError("Titular demasiado ancho para miniatura")


def crear_portada_gta(plan, texto, formato, destino, variante=0, banco=BANCO_ROCKSTAR):
    if formato not in ("short", "largo"):
        raise ValueError("Formato de portada inválido")
    if not 0 <= variante <= 2:
        raise ValueError("Variante inválida")
    destino = Path(destino)
    w, h = (1280, 720) if formato == "largo" else (720, 1280)
    pedido = plan.get("portada_paleta", "fucsia")
    claves = list(PALETAS)
    paleta = PALETAS.get(pedido, PALETAS["fucsia"])
    # Las tres alternativas difieren visualmente incluso si usan la misma foto.
    if variante:
        base_idx = claves.index(pedido) if pedido in PALETAS else 0
        paleta = PALETAS[claves[(base_idx + variante) % len(claves)]]
    neon, secundario, tinta = paleta["neon"], paleta["secondary"], paleta["ink"]
    img = Image.new("RGB", (w, h), tinta)
    foto = elegir_foto(plan, banco=banco)
    if foto is not None:
        try:
            with Image.open(foto) as original:
                frame = ImageOps.fit(
                    original.convert("RGB"), (w, h),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.55, 0.43) if formato == "short" else (0.58, 0.5)
                )
            frame = ImageEnhance.Contrast(frame).enhance(1.20)
            frame = ImageEnhance.Color(frame).enhance(1.27)
            img.paste(frame)
        except (OSError, ValueError):
            foto = None
    if foto is None:
        d = ImageDraw.Draw(img)
        for n in range(10):
            x = int(n*w/9)
            d.polygon([(x, 0), (x+int(w*.13), 0),
                       (x-int(w*.25), h), (x-int(w*.39), h)],
                      fill=tuple(min(255, v + (n % 3)*9) for v in tinta))
    # Degradado translúcido: fotografía visible, texto siempre legible.
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = ImageDraw.Draw(overlay)
    if formato == "largo":
        for x in range(w):
            k = x / w
            alpha = int(229*(1-k)**2 + 25)
            o.line((x, 0, x, h), fill=(*tinta, min(245, alpha)))
        # El personaje o paisaje queda protagonista a la derecha.
        caja = (35, 30, int(w*.67), h-30)
    else:
        for y in range(h):
            k = y / h
            alpha = int(20 + 223*k**2.3)
            o.line((0, y, w, y), fill=(*tinta, min(242, alpha)))
        caja = (30, int(h*.54), w-30, h-40)
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    d = ImageDraw.Draw(img)
    # Contorno de alto contraste + barra de marca minimalista.
    borde = max(7, int(w*.009))
    d.rounded_rectangle((8, 8, w-9, h-9), radius=22,
                        outline=neon, width=borde)
    d.rounded_rectangle((23, 25, 232 if formato == "largo" else 222, 76),
                        radius=11, fill=(*tinta, 220), outline=secundario, width=3)
    d.text((35, 35), "PÍXEL FEROZ", font=fuente_dejavu(20, True), fill=secundario)
    # Titular 2–5 palabras, trazo y sombra; sin tapar media fotografía.
    titulo = titular_breve(texto)
    if formato == "largo":
        x0, y0, ancho = 54, 218, int(w*.52)
        tam, max_lineas = 105, 3
    else:
        x0, y0, ancho = 44, int(h*.69), w-88
        tam, max_lineas = 75, 3
    f, lineas = ajustar_fuente(d, titulo, ancho, max_lineas, tam)
    salto = int(f.size*1.20)
    if formato == "short":
        y0 = min(y0, int(h*.87)-len(lineas)*salto)
    for linea in lineas:
        d.text((x0+5, y0+7), linea, font=f, fill=(2, 4, 12, 235),
               stroke_width=9, stroke_fill=(2, 4, 12, 220))
        d.text((x0, y0), linea, font=f, fill=(255, 255, 255, 255),
               stroke_width=3, stroke_fill=tuple(neon)+(255,))
        y0 += salto
    # Subrayado luminoso e identificador breve para continuidad del canal.
    ybarra = int(h*.91) if formato == "short" else int(h*.87)
    d.rounded_rectangle((x0, ybarra, x0+int(w*.24), ybarra+13),
                        radius=6, fill=secundario)
    d.text((x0, ybarra+23), "GTA VI", font=fuente_dejavu(30 if formato=="largo" else 28, True), fill=neon)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # JPEG RGB, calidad optimizada y segura para el límite de 2 MB.
    resultado = img.convert("RGB")
    calidad = 89
    while calidad >= 53:
        resultado.save(destino, "JPEG", quality=calidad, optimize=True)
        if destino.stat().st_size <= 2_000_000:
            return destino
        calidad -= 9
    raise RuntimeError("Miniatura supera 2 MB incluso comprimida")
