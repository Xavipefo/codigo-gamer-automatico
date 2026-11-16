#!/usr/bin/env python3
"""Control antes de autorizar subida a YouTube: vídeo, fuentes y metadatos."""
import argparse
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

BASE=Path(__file__).resolve().parent
OUT=BASE/"salida"
THEMES=BASE/"temas_verificados.json"


def comprobar(formato):
    if not shutil.which("ffprobe"):
        raise RuntimeError("Se necesita ffprobe")
    plan=json.loads((OUT/"plan.json").read_text(encoding="utf-8"))
    assert plan["formato"]==formato, "Formato no coincide"
    assert plan["publicacion_automatica"] is False, "Publicación automática no bloqueada"
    assert plan["estado"]=="BORRADOR_PENDIENTE_REVISION", "Plan editorial inválido"
    temas=json.loads(THEMES.read_text(encoding="utf-8"))
    tema=next((t for t in temas if t["id"]==plan["tema_id"]),None)
    if tema is None:
        raise ValueError("Tema no existe en listado verificado")
    if tema.get("vigente_hasta") and date.fromisoformat(tema["vigente_hasta"])<date.today():
        raise ValueError("Tema caducado")
    for hecho in tema["hechos"]:
        if not hecho.get("fuente","").startswith("https://"):
            raise ValueError("Hay una afirmación sin fuente HTTPS")
    guion=(OUT/"guion.txt").read_text(encoding="utf-8").strip()
    if len(guion.split()) < (50 if formato=="short" else 650):
        raise ValueError("Guion demasiado corto")
    video=OUT/("codigo_gamer_short.mp4" if formato=="short" else "codigo_gamer_largo.mp4")
    if video.stat().st_size < 20000:
        raise ValueError("Vídeo pequeño o vacío")
    p=subprocess.run(["ffprobe","-v","error","-show_streams","-show_format",
                      "-of","json",str(video)],check=True,capture_output=True,text=True)
    info=json.loads(p.stdout)
    streams=info.get("streams",[])
    v=next((s for s in streams if s.get("codec_type")=="video"),None)
    a=next((s for s in streams if s.get("codec_type")=="audio"),None)
    if not v or not a:
        raise ValueError("Faltan audio o vídeo")
    expected=(720,1280) if formato=="short" else (1280,720)
    if (v.get("width"),v.get("height"))!=expected:
        raise ValueError("Resolución incorrecta")
    dur=float(info["format"]["duration"])
    bounds=(10,180) if formato=="short" else (180,1200)
    if not bounds[0]<=dur<=bounds[1]:
        raise ValueError(f"Duración {dur:.1f}s fuera de {bounds}")
    mini=OUT/"miniatura.jpg"
    if not mini.exists() or mini.stat().st_size>2*1024*1024:
        raise ValueError("Miniatura ausente o demasiado grande")
    result={"tema":plan["tema_id"],"formato":formato,"segundos":round(dur,2),
            "resolucion":list(expected),"audio":True,"fuentes":len(tema["hechos"]),
            "revision_humana_pendiente":True,"listo_para_subida_privada":True}
    (OUT/"calidad.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--formato",choices=("short","largo"),required=True)
    args=p.parse_args()
    comprobar(args.formato)
