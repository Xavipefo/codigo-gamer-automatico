#!/usr/bin/env python3
"""Clips oficiales breves de Rockstar GTA VI para montajes PRIVADOS revisables.

Rockstar permite descargarlos/compartirlos desde su página de prensa,
pero eso NO concede licencia comercial general. No descarga YouTube.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

URL="https://media-rockstargames-com.akamaized.net/VI/downloads/videos/GTAVI_Videos.zip"
FUENTE="https://www.rockstargames.com/VI/media/videos"
CREDITO="Rockstar Games — clips oficiales GTA VI"
BASE=Path(__file__).resolve().parent / ".cache" / "rockstar_clips"
MAX_ZIP=850*1024*1024
MAX_EXTRAIDO=2400*1024*1024

class SinRedirigir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise RuntimeError("La URL oficial del ZIP redirige; revisar la fuente")

def descargar(destino):
    destino.parent.mkdir(parents=True,exist_ok=True)
    if destino.is_file():
        try:
            with zipfile.ZipFile(destino) as zf:
                if len(zf.infolist())>=4 and zf.testzip() is None:
                    return
        except (OSError,zipfile.BadZipFile):
            pass
        destino.unlink(missing_ok=True)
    u=urllib.parse.urlsplit(URL)
    if u.scheme!="https" or u.hostname!="media-rockstargames-com.akamaized.net":
        raise RuntimeError("Dominio del ZIP de clips no admitido")
    temporal=destino.with_suffix(".part")
    try:
        op=urllib.request.build_opener(SinRedirigir())
        req=urllib.request.Request(URL, headers={"User-Agent":"PixelFerozEditorial/1.0"})
        with op.open(req,timeout=90) as resp, temporal.open("wb") as out:
            while True:
                bloque=resp.read(1024*1024)
                if not bloque:
                    break
                out.write(bloque)
                if out.tell()>MAX_ZIP:
                    raise RuntimeError("ZIP de clips demasiado grande")
        with zipfile.ZipFile(temporal) as zf:
            if len(zf.infolist())<4:
                raise RuntimeError("ZIP oficial sin clips suficientes")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)

def duracion_mp4(ruta):
    r=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams",
                       "-of","json",str(ruta)],capture_output=True,text=True,
                     check=True,timeout=35)
    info=json.loads(r.stdout)
    if not any(x.get("codec_type")=="video" for x in info.get("streams",[])):
        raise ValueError("Sin pista de vídeo")
    segundos=float(info.get("format",{}).get("duration",0))
    if not 1.5<=segundos<=240:
        raise ValueError("Duración de vídeo inesperada")
    return round(segundos,2)

def preparar(base=BASE):
    base=Path(base)
    indice=base/"catalogo_clips.json"
    if indice.is_file():
        try:
            datos=json.loads(indice.read_text(encoding="utf-8"))
            if (datos.get("fuente")==FUENTE and len(datos.get("clips",[]))>=4
                 and all((base/x["archivo"]).is_file() for x in datos["clips"])):
                return datos
        except (ValueError,TypeError,KeyError):
            pass
    archivo=base/"GTAVI_Videos.zip"
    descargar(archivo)
    carpeta=base/"videos"
    carpeta.mkdir(exist_ok=True)
    entradas=[]
    acumulado=0
    with zipfile.ZipFile(archivo) as zf:
        miembros=zf.infolist()
        if len(miembros)>90:
            raise RuntimeError("Demasiados archivos en ZIP oficial")
        for item in miembros:
            acumulado+=item.file_size
            if acumulado>MAX_EXTRAIDO or item.file_size>600*1024*1024:
                raise RuntimeError("Los clips superan los límites de tamaño")
            if item.is_dir():
                continue
            ruta=Path(item.filename)
            if ruta.is_absolute() or ".." in ruta.parts or ruta.suffix.lower() not in (".mp4",".mov",".webm"):
                continue
            clave=hashlib.sha256(item.filename.encode("utf-8")).hexdigest()[:12]
            destino=carpeta/(clave+ruta.suffix.lower())
            with zf.open(item) as src, destino.open("wb") as dst:
                shutil.copyfileobj(src,dst,length=1024*1024)
            try:
                segundos=duracion_mp4(destino)
            except (ValueError,OSError,subprocess.SubprocessError):
                destino.unlink(missing_ok=True)
                continue
            entradas.append({"archivo":str(destino.relative_to(base)),
                             "nombre":ruta.stem,"segundos":segundos})
    if len(entradas)<4:
        raise RuntimeError("No se validaron cuatro clips oficiales")
    datos={"fuente":FUENTE,"archivo_oficial":URL,"creditos":CREDITO,
           "derechos":"Descargable desde Rockstar; no autoriza por sí solo uso comercial.",
           "clips":entradas}
    indice.write_text(json.dumps(datos,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Clips oficiales preparados:",len(entradas),flush=True)
    return datos

def cargar(base=BASE):
    base=Path(base)
    indice=base/"catalogo_clips.json"
    if not indice.is_file():
        return []
    datos=json.loads(indice.read_text(encoding="utf-8"))
    if datos.get("fuente")!=FUENTE:
        raise RuntimeError("Origen de clips no verificado")
    salida=[]
    for item in datos["clips"]:
        ruta=(base/item["archivo"]).resolve()
        if not ruta.is_relative_to(base.resolve()) or not ruta.is_file():
            raise RuntimeError("Ruta inválida en banco oficial de vídeos")
        salida.append({"ruta":ruta,"credito":CREDITO,
                       "segundos":item["segundos"],"nombre":item["nombre"],
                       "origen":"oficial_descargable_revision_privada"})
    return salida

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--preparar",action="store_true")
    args=p.parse_args()
    datos=preparar() if args.preparar else {"clips":cargar()}
    print("Recursos de vídeo oficiales:",len(datos["clips"]))

if __name__=="__main__":
    main()
