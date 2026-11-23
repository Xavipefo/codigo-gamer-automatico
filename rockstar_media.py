#!/usr/bin/env python3
"""Banco de capturas PÚBLICAS oficiales de GTA VI para revisión editorial.

El enlace oficial permite descargar/compartir el archivo, NO garantiza una
licencia comercial. Solo vídeos privados y revisión humana de derechos.
No usa material filtrado ni extrae contenidos de YouTube.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps
from generar_short import fuente, partir_lineas

SOURCE = "https://www.rockstargames.com/VI/media/screenshots"
MEDIA_PAGE = "https://www.rockstargames.com/VI/media"
POLICY = "https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material"
ZIP_URL = "https://media-rockstargames-com.akamaized.net/VI/downloads/screenshots/GTAVI_Screenshots.zip"
CREDITO = "Rockstar Games — imágenes oficiales de Grand Theft Auto VI"
BASE = Path(__file__).resolve().parent / ".cache" / "rockstar"
MAX_ARCHIVO = 450 * 1024 * 1024
MAX_EXTRAIDO = 1800 * 1024 * 1024
CLAVES = {
    "ultimate": ("ultimate", "edition", "grotti", "cheetah"),
    "vintage": ("vintage", "bonus", "stanier"),
    "artwork": ("arte", "portada", "launch", "trailer"),
    "duo": ("jason", "lucia"),
    "jason": ("jason", "duval"),
    "lucia": ("lucia", "caminos"),
    "vice": ("vice", "city", "ciudad", "mapa"),
    "leonida": ("leonida", "keys"),
    "grassrivers": ("grassrivers", "pantano"),
    "port": ("gellhorn", "port"),
    "ambrosia": ("ambrosia",),
    "kalaga": ("kalaga", "montana"),
    "real": ("real", "dimez"),
    "boobie": ("boobie", "ike"),
    "drequan": ("drequan", "priest"),
    "cal": ("cal", "hampton"),
    "brian": ("brian", "heder"),
    "raul": ("raul", "bautista"),
}

def normalizar(s):
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode("ascii")

def etiqueta(nombre):
    return re.sub(r"[^a-z0-9]+", "-", normalizar(nombre)).strip("-")[:70]

def categoria(nombre):
    n = normalizar(nombre).replace("_", " ").replace("-", " ")
    if "jason" in n and "lucia" in n:
        return "duo"
    for key, aliases in CLAVES.items():
        if key == "duo":
            continue
        if any(a in n.split() for a in aliases):
            return key
    return "general"

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Nunca descargar desde dominios inesperados.
        raise RuntimeError("La descarga oficial redirigió: revisar manualmente el enlace.")

def descargar_zip(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.is_file():
        try:
            with zipfile.ZipFile(ruta) as zf:
                if zf.testzip() is None and len(zf.infolist()) >= 12:
                    return
        except (OSError, zipfile.BadZipFile):
            pass
        ruta.unlink(missing_ok=True)
    url = urllib.parse.urlsplit(ZIP_URL)
    if url.scheme != "https" or url.hostname != "media-rockstargames-com.akamaized.net":
        raise RuntimeError("La fuente multimedia no es el dominio oficial previsto")
    opener = urllib.request.build_opener(NoRedirect())
    temp = ruta.with_suffix(".part")
    try:
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "PixelFerozEditorial/1.0"})
        with opener.open(req, timeout=90) as resp, temp.open("wb") as dst:
            while True:
                bloque = resp.read(1024 * 1024)
                if not bloque:
                    break
                dst.write(bloque)
                if dst.tell() > MAX_ARCHIVO:
                    raise RuntimeError("El ZIP oficial supera el límite de tamaño")
        if temp.stat().st_size < 100_000:
            raise RuntimeError("ZIP oficial incompleto")
        with zipfile.ZipFile(temp) as zf:
            if len(zf.infolist()) < 12:
                raise RuntimeError("ZIP oficial sin capturas suficientes")
        temp.replace(ruta)
    finally:
        temp.unlink(missing_ok=True)

def preparar_banco(base=BASE):
    base = Path(base)
    index = base / "catalogo.json"
    if index.is_file():
        try:
            datos = json.loads(index.read_text(encoding="utf-8"))
            if (datos.get("origen") == SOURCE and len(datos.get("imagenes", [])) >= 12
                    and all((base / d["archivo"]).is_file() for d in datos["imagenes"])):
                return datos
        except (ValueError, KeyError, TypeError):
            pass
    archivo = base / "GTAVI_Screenshots.zip"
    descargar_zip(archivo)
    imagenes = []
    carpeta = base / "imagenes"
    carpeta.mkdir(parents=True, exist_ok=True)
    total_extraido = 0
    with zipfile.ZipFile(archivo) as zf:
        miembros = zf.infolist()
        if len(miembros) > 500:
            raise RuntimeError("Demasiadas entradas en ZIP oficial")
        for member in miembros:
            total_extraido += member.file_size
            if member.file_size > 50 * 1024 * 1024 or total_extraido > MAX_EXTRAIDO:
                raise RuntimeError("ZIP supera límite de recursos descomprimidos")
            if member.is_dir():
                continue
            p = Path(member.filename)
            if ".." in p.parts or p.is_absolute() or p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            if member.file_size < 1000:
                continue
            nombre = p.stem
            # Respetar el título del ZIP, sin asumir que los números identifican gameplay.
            clave = hashlib.sha256(member.filename.encode("utf-8")).hexdigest()[:12]
            ruta = carpeta / ((etiqueta(nombre) or "captura") + "-" + clave + ".jpg")
            try:
                with zf.open(member) as src, Image.open(src) as im:
                    if min(im.size) < 480 or im.width * im.height > 40_000_000:
                        continue
                    foto = ImageOps.exif_transpose(im).convert("RGB")
                    foto.thumbnail((1920, 1280), Image.Resampling.LANCZOS)
                    foto.save(ruta, quality=85, optimize=True)
            except (OSError, ValueError):
                continue
            imagenes.append({
                "archivo": str(ruta.relative_to(base)),
                "nombre": nombre,
                "categoria": categoria(nombre),
                "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()
            })
    if len(imagenes) < 12:
        raise RuntimeError("No hay 12 capturas oficiales verificables; producción bloqueada")
    datos = {
        "origen": SOURCE,
        "archivo_oficial": ZIP_URL,
        "pagina_oficial": MEDIA_PAGE,
        "creditos": CREDITO,
        "politica_derechos": POLICY,
        "nota_derechos": "Compartible desde la galería; NO implica permiso comercial general.",
        "imagenes": imagenes
    }
    index.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Banco GTA VI oficial verificado:", len(imagenes), "imágenes", flush=True)
    return datos

def cargar_banco(base=BASE):
    base = Path(base)
    path = base / "catalogo.json"
    if not path.is_file():
        raise RuntimeError("Falta el banco oficial: ejecutar antes rockstar_media.py --preparar")
    datos = json.loads(path.read_text(encoding="utf-8"))
    fotos = datos.get("imagenes", [])
    if datos.get("origen") != SOURCE or len(fotos) < 12:
        raise RuntimeError("Catálogo de Rockstar incompleto")
    for item in fotos:
        path = (base / item["archivo"]).resolve()
        if not path.is_relative_to(base.resolve()) or not path.is_file():
            raise RuntimeError("Ruta del banco oficial inválida")
    return datos

def elegir_imagenes(plan, escenas, base=BASE):
    """Relevancia por escena + variedad real; evita 4 fotos seguidas del mismo personaje."""
    datos = cargar_banco(base)
    fotos = datos["imagenes"]
    exclusivas=plan.get("categorias_visuales_exclusivas") or []
    if exclusivas:
        if not isinstance(exclusivas,list) or any(
            not isinstance(x,str) or x not in CLAVES for x in exclusivas
        ):
            raise ValueError("Categorías visuales exclusivas desconocidas")
        fotos=[x for x in fotos if x["categoria"] in exclusivas]
        if len(fotos)<max(5,(len(escenas)+1)//2):
            raise RuntimeError(
                "No hay suficientes fotografías OFICIALES del tema concreto; "
                "se bloquea en lugar de mostrar zonas ajenas"
            )
    usados = set()
    resultado = []
    categorias_previas = []
    contexto = normalizar(plan.get("titulo_propuesto", "") + " " + plan.get("tema_id", ""))
    tokens_contexto = set(re.findall(r"[a-z0-9]+", contexto))
    preferidos = [p for p in plan.get("visuales_preferidos", []) if p in CLAVES]
    for i, escena in enumerate(escenas):
        texto = normalizar(escena["texto"])
        tokens_escena = set(re.findall(r"[a-z0-9]+", texto))
        preferida = preferidos[i % len(preferidos)] if preferidos else None
        puntuadas = []
        for item in fotos:
            cat = item["categoria"]
            aliases = CLAVES.get(cat, (cat,))
            puntuacion = sum(11 for a in aliases if a in tokens_escena)
            puntuacion += sum(2 for a in aliases if a in tokens_contexto)
            nombre = set(re.findall(r"[a-z0-9]+", normalizar(item["nombre"])))
            puntuacion += min(4, len(nombre & tokens_escena))
            if preferidos and cat in preferidos:
                puntuacion += 2
            if cat == preferida:
                puntuacion += 9
            if len(categorias_previas) >= 2 and categorias_previas[-2:] == [cat, cat]:
                puntuacion -= 26
            if item["archivo"] in usados:
                puntuacion -= 80
            desempate = int(hashlib.sha256(
                (item["archivo"] + str(i)).encode("utf-8")
            ).hexdigest()[:8], 16)
            puntuadas.append((puntuacion, desempate, item))
        ganador = max(puntuadas, key=lambda x: (x[0], x[1]))[2]
        usados.add(ganador["archivo"])
        categorias_previas.append(ganador["categoria"])
        resultado.append((Path(base) / ganador["archivo"], CREDITO, ganador["nombre"]))
    return resultado

def muestra_equilibrada(imagenes, cantidad=36):
    """Muestra ubicaciones y protagonistas, no solo los primeros del ZIP."""
    prioridad = (
        "vice", "duo", "jason", "lucia", "leonida", "grassrivers", "port",
        "ultimate", "vintage", "artwork",
        "ambrosia", "kalaga", "cal", "brian", "raul", "boobie",
        "drequan", "real", "general"
    )
    grupos = {k: [] for k in prioridad}
    for item in imagenes:
        grupos.setdefault(item["categoria"], []).append(item)
    elegidas = []
    while len(elegidas) < cantidad and any(grupos.values()):
        for categoria_actual in grupos:
            if grupos[categoria_actual] and len(elegidas) < cantidad:
                elegidas.append(grupos[categoria_actual].pop(0))
    return elegidas


def crear_contacto(datos, base, salida, max_imagenes=36):
    """Contact sheet con índice y nombres; útil para análisis en el chat."""
    base, salida = Path(base), Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    items = muestra_equilibrada(datos["imagenes"], max_imagenes)
    cols, w, h = 4, 300, 208
    rows = (len(items) + cols - 1) // cols
    atlas = Image.new("RGB", (cols*w, max(1,rows)*h), (12, 21, 34))
    d = ImageDraw.Draw(atlas)
    f = fuente(18, True)
    for i, item in enumerate(items):
        x, y = (i % cols)*w, (i//cols)*h
        with Image.open(base/item["archivo"]) as im:
            thumb = ImageOps.fit(im.convert("RGB"), (w-8, h-43))
            atlas.paste(thumb, (x+4, y+4))
        txt = (item["nombre"][:31] or item["categoria"])
        d.text((x+8,y+h-34), f"{i+1:02d}. {txt}", font=f, fill=(240,246,252))
    atlas.save(salida/"contacto_rockstar.jpg", quality=85)
    (salida/"catalogo_rockstar.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preparar", action="store_true")
    ap.add_argument("--revision", action="store_true")
    ap.add_argument("--base", type=Path, default=BASE)
    ap.add_argument("--salida", type=Path, default=Path("salida/revision_visual"))
    args = ap.parse_args()
    if args.preparar:
        datos = preparar_banco(args.base)
    else:
        datos = cargar_banco(args.base)
    if args.revision:
        crear_contacto(datos, args.base, args.salida)
    print("Imágenes oficiales disponibles:", len(datos["imagenes"]))

if __name__ == "__main__":
    main()
