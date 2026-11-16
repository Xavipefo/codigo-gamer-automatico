#!/usr/bin/env python3
"""Actualiza el historial ÚNICAMENTE a partir de una subida verificada como privada."""
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
OUT=BASE/"salida"
HISTORIAL=BASE/"historial_publicados.json"


def main():
    archivo=OUT/"youtube_resultado.json"
    dato=json.loads(archivo.read_text(encoding="utf-8"))
    if dato.get("estado")!="subido" or dato.get("privacidad_verificada")!="private":
        raise ValueError("Sólo se registran subidas con estado privado verificado")
    historial=json.loads(HISTORIAL.read_text(encoding="utf-8")) if HISTORIAL.exists() else []
    if not isinstance(historial,list):
        raise ValueError("Historial no válido")
    if any(x.get("video_id")==dato["video_id"] for x in historial):
        print("El video ya figura en el historial")
        return
    if any(x.get("tema_id")==dato["tema_id"] and x.get("estado") in ("subido","publicado")
           for x in historial):
        raise ValueError("El tema ya tiene una subida anterior")
    historial.append(dato)
    HISTORIAL.write_text(json.dumps(historial,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Historial actualizado:",dato["video_id"])


if __name__=="__main__":
    main()
