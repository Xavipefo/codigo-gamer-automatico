#!/usr/bin/env python3
"""Descubre candidatos de noticias en fuentes oficiales.

Sólo crea propuestas; nunca las publica ni las convierte en hechos confirmados.
"""
import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

BASE=Path(__file__).resolve().parent
DEST=BASE/"propuestas_noticias.json"
FUENTES={
    "PlayStation Blog":"https://blog.playstation.com/feed/",
    "Xbox Wire":"https://news.xbox.com/en-us/feed/",
}
DOMINIOS=("blog.playstation.com","news.xbox.com")
TAGS={"gta","grand theft auto","rockstar","videojuego","videogame",
      "games","gaming","playstation","xbox"}
HEADERS={"User-Agent":"PixelFerozEditorial/1.0 (research; no automatic publishing)"}


def extraer_xml(url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=20) as res:
        if int(res.status)!=200:
            raise RuntimeError("Respuesta HTTP "+str(res.status))
        if res.headers.get("Content-Length") and int(res.headers["Content-Length"])>2_000_000:
            raise ValueError("Feed demasiado grande")
        contenido=res.read(2_000_001)
        if len(contenido)>2_000_000:
            raise ValueError("Feed excede límite")
    return ET.fromstring(contenido)


def texto(elem,ruta):
    v=elem.find(ruta)
    return "".join(v.itertext()).strip() if v is not None else ""


def dominio_valido(url):
    u=urlparse(url)
    d=(u.hostname or "").lower()
    return u.scheme=="https" and d in DOMINIOS


def noticias():
    resultados=[]
    for origen,url in FUENTES.items():
        try:
            raiz=extraer_xml(url)
            candidatos=raiz.findall(".//item")
            if not candidatos:
                candidatos=raiz.findall(".//{http://www.w3.org/2005/Atom}entry")
            for e in candidatos[:35]:
                titulo=texto(e,"title") or texto(e,"{http://www.w3.org/2005/Atom}title")
                enlace=texto(e,"link")
                if not enlace:
                    link=e.find("{http://www.w3.org/2005/Atom}link")
                    enlace=link.attrib.get("href","") if link is not None else ""
                titulo=unescape(re.sub(r"\s+"," ",titulo)).strip()
                if not titulo or not dominio_valido(enlace):
                    continue
                if not any(x in titulo.lower() for x in TAGS):
                    continue
                resultados.append({
                    "titulo":titulo[:180],"url":enlace,"origen":origen,
                    "estado":"pendiente_verificacion_humana",
                    "detectado_utc":datetime.now(timezone.utc).isoformat()
                })
        except (OSError,ET.ParseError,ValueError,RuntimeError) as exc:
            print("Aviso: fuente no disponible:",origen,type(exc).__name__)
    unicos={x["url"]:x for x in resultados}
    return list(unicos.values())


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--salida",type=Path,default=DEST)
    args=p.parse_args()
    registros=noticias()
    args.salida.write_text(json.dumps(registros,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Candidatos pendientes de revisión:",len(registros))
    print("No se han añadido temas confirmados ni se ha publicado contenido.")


if __name__=="__main__":
    main()
