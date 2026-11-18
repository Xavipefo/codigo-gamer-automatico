#!/usr/bin/env python3
"""Complementos oficiales: Ultimate Edition, Vintage Vice City y arte promocional.

Descarga solo ZIPs públicos enlazados en Rockstar Games, sin extracción
de plataformas. Son recursos editoriales para revisión PRIVADA.
"""
import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from PIL import Image, ImageOps

from rockstar_media import BASE, SOURCE, preparar_banco, etiqueta, NoRedirect

PAQUETES = {
 "ultimate":"https://media-rockstargames-com.akamaized.net/VI/downloads/screenshots/GTAVI_Ultimate_Edition_Benefits.zip",
 "vintage":"https://media-rockstargames-com.akamaized.net/VI/downloads/screenshots/GTAVI_Vintage_Vice_City_Pack.zip",
 "artwork":"https://media-rockstargames-com.akamaized.net/VI/downloads/artwork_wallpapers/GTAVI_Artwork_Wallpapers.zip",
}
LIMITE_ZIP=420*1024*1024
LIMITE_TOTAL=950*1024*1024

def descargar(url, destino):
    if url not in PAQUETES.values():
        raise ValueError("URL que no consta entre los recursos oficiales")
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname!="media-rockstargames-com.akamaized.net":
        raise ValueError("Dominio externo no autorizado")
    if destino.is_file():
        try:
            with zipfile.ZipFile(destino) as zf:
                if len(zf.infolist()) >= 4 and zf.testzip() is None:
                    return
        except (OSError,zipfile.BadZipFile):
            destino.unlink(missing_ok=True)
    destino.parent.mkdir(parents=True,exist_ok=True)
    temporal=destino.with_suffix(".part")
    try:
        op=urllib.request.build_opener(NoRedirect())
        req=urllib.request.Request(url,headers={"User-Agent":"PixelFerozEditorial/1.0"})
        with op.open(req,timeout=90) as r, temporal.open("wb") as out:
            while True:
                trozo=r.read(1024*1024)
                if not trozo:
                    break
                out.write(trozo)
                if out.tell()>LIMITE_ZIP:
                    raise RuntimeError("Paquete visual complementario demasiado grande")
        with zipfile.ZipFile(temporal) as zf:
            if len(zf.infolist())<4:
                raise RuntimeError("No hay suficientes imágenes oficiales")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)

def preparar(base=BASE):
    base=Path(base)
    datos=preparar_banco(base)
    instalados=set(datos.get("paquetes_extra",[]))
    for tipo,url in PAQUETES.items():
        if tipo in instalados:
            continue
        archivo=base/(tipo+".zip")
        try:
            descargar(url,archivo)
            nuevos=[]
            total=0
            with zipfile.ZipFile(archivo) as zf:
                miembros=zf.infolist()
                if len(miembros)>400:
                    raise RuntimeError("Demasiados archivos complementarios")
                for item in miembros:
                    total+=item.file_size
                    if total>LIMITE_TOTAL or item.file_size>45*1024*1024:
                        raise RuntimeError("ZIP complementario excede los límites")
                    path=Path(item.filename)
                    if (item.is_dir() or path.is_absolute() or ".." in path.parts
                        or path.suffix.lower() not in (".jpg",".jpeg",".webp",".png")):
                        continue
                    clave=hashlib.sha256(item.filename.encode()).hexdigest()[:10]
                    destino=base/"imagenes"/(tipo+"-"+etiqueta(path.stem)+"-"+clave+".jpg")
                    try:
                        with zf.open(item) as src, Image.open(src) as im:
                            if min(im.size)<480 or im.width*im.height>45_000_000:
                                continue
                            foto=ImageOps.exif_transpose(im).convert("RGB")
                            foto.thumbnail((1920,1280),Image.Resampling.LANCZOS)
                            foto.save(destino,quality=85,optimize=True)
                    except (OSError, ValueError):
                        continue
                    nuevos.append({
                        "archivo":str(destino.relative_to(base)),
                        "nombre":tipo.upper()+": "+path.stem,
                        "categoria":tipo,
                        "sha256":hashlib.sha256(destino.read_bytes()).hexdigest(),
                        "pagina_publica":"https://www.rockstargames.com/VI/media"
                    })
            if len(nuevos)<4:
                raise RuntimeError("Paquete sin imágenes suficientes")
            datos["imagenes"].extend(nuevos)
            datos.setdefault("paquetes_extra",[]).append(tipo)
            (base/"catalogo.json").write_text(
                json.dumps(datos,ensure_ascii=False,indent=2)+"\n",
                encoding="utf-8"
            )
            print("Complemento oficial",tipo,":",len(nuevos),"imágenes",flush=True)
        except (OSError,ValueError,RuntimeError,zipfile.BadZipFile) as e:
            print("::warning::No se pudo añadir el paquete",tipo,":",str(e),flush=True)
    return datos

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--preparar",action="store_true")
    args=ap.parse_args()
    if args.preparar:
        d=preparar()
        print("Total imágenes disponibles:",len(d["imagenes"]))
