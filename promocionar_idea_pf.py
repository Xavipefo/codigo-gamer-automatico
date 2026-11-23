#!/usr/bin/env python3
"""PF-90: promociona una idea de investigación SOLO tras revisar sus fuentes.

Nunca publica, genera ni da por confirmados automáticamente hechos inventados.
La ficha se prepara y verifica antes de invocar el comando.
"""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from preparar_contenido import validar_tema

BASE = Path(__file__).resolve().parent

def leer(path):
    v=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(v,list):
        raise ValueError("Se esperaba una lista editorial")
    return v

def guardar(path,contenido):
    path.write_text(json.dumps(contenido,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def promocionar(ficha,confirmacion,base=BASE):
    if confirmacion!="FUENTES_REVISADAS":
        raise PermissionError("Hace falta confirmar FUENTES_REVISADAS tras contrastar cada hecho")
    base=Path(base)
    candidato=json.loads(Path(ficha).read_text(encoding="utf-8"))
    ident=candidato.get("id","")
    if not isinstance(ident,str) or not re.fullmatch(r"[a-z0-9_-]{3,60}",ident):
        raise ValueError("ID inválido")
    catalogo=base/"temas_verificados.json"
    if ident in {x.get("id") for x in leer(catalogo)}:
        raise ValueError("ID ya confirmado")
    formato=candidato.get("formato")
    if formato not in ("short","largo"):
        raise ValueError("Indica el formato de la idea")
    ideas=base/"colas"/("ideas_shorts_3meses.json" if formato=="short" else "ideas_documentales_3meses.json")
    propuestas=leer(ideas)
    actual=next((x for x in propuestas if x["id"]==ident),None)
    if actual is None or actual.get("estado")!="pendiente_verificacion":
        raise ValueError("La idea no existe en el backlog o ya fue promovida")
    if actual["formato"]!=formato:
        raise ValueError("La ficha no coincide con el formato")
    if candidato.get("titulo")!=actual["titulo"]:
        raise ValueError("No sustituir el título sin actualizar primero la idea editorial")
    tema={
        "id":ident,
        "titulo":candidato["titulo"],
        "formatos":[formato],
        "estado":"confirmado",
        "fecha_verificacion":date.today().isoformat(),
        "gancho":candidato["gancho"],
        "contexto":candidato["contexto"],
        "hechos":candidato["hechos"],
        "texto_miniatura":candidato.get("texto_miniatura",candidato["titulo"])[:90],
        "visuales_preferidos":candidato.get("visuales_preferidos",[]),
        "portada_paleta":candidato.get("portada_paleta","fucsia"),
        "portada_categoria":candidato.get("portada_categoria","artwork"),
    }
    if formato=="largo":
        tema["esquema_largo"]=candidato["esquema_largo"]
        tema["miniatura_opciones"]=candidato.get("miniatura_opciones",[])
    validar_tema(tema)
    if len(tema["hechos"])<2 or len({x["fuente"] for x in tema["hechos"]})<1:
        raise ValueError("Faltan afirmaciones y fuentes independientes revisadas")
    if not tema["visuales_preferidos"]:
        raise ValueError("Indica recursos visuales realmente disponibles")
    queue=base/"colas"/("shorts.json" if formato=="short" else "documentales.json")
    cola=leer(queue)
    if ident in cola:
        raise ValueError("Tema ya reservado")
    plan=base/"colas"/"calendario_3meses.json"
    calendario=json.loads(plan.read_text(encoding="utf-8"))
    for slot in calendario["slots"]:
        if slot["tema_id"]==ident:
            slot["estado"]="tema_confirmado"
    pendientes=[x for x in propuestas if x["id"]!=ident]
    confirmed=leer(catalogo)
    # Las cuatro escrituras son del mismo commit una vez lanzado desde GitHub.
    guardar(catalogo,confirmed+[tema])
    guardar(queue,cola+[ident])
    guardar(ideas,pendientes)
    plan.write_text(json.dumps(calendario,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return ident

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--ficha",type=Path,required=True)
    p.add_argument("--confirmacion",default="")
    args=p.parse_args()
    print("Tema promocionado sin publicar:",promocionar(args.ficha,args.confirmacion))

if __name__=="__main__":
    main()
