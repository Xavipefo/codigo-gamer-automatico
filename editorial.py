"""Selección editorial, deduplicación y guiones para Código Gamer.

No genera hechos: solo utiliza afirmaciones verificadas previamente por un editor.
"""
import argparse
import hashlib
import json
import os
import re
from datetime import date
from pathlib import Path

from preparar_contenido import preparar, validar_tema

BASE = Path(__file__).resolve().parent
TEMAS = BASE / "temas_verificados.json"
HISTORIAL = BASE / "historial_publicados.json"
SALIDA = BASE / "salida"


def cargar_historial():
    if not HISTORIAL.exists():
        return []
    valor = json.loads(HISTORIAL.read_text(encoding="utf-8"))
    if not isinstance(valor, list):
        raise ValueError("El historial debe ser una lista JSON")
    return valor


def cargar_elegibles():
    datos = json.loads(TEMAS.read_text(encoding="utf-8"))
    if not isinstance(datos, list):
        raise ValueError("temas_verificados.json debe ser una lista")
    opciones = []
    for t in datos:
        if not isinstance(t, dict):
            continue
        vence = t.get("vigente_hasta")
        if vence and date.fromisoformat(vence) < date.today():
            continue
        if t.get("estado") != "confirmado":
            continue
        # Fallar si hay datos incorrectos, no publicar silenciosamente.
        validar_tema(t)
        opciones.append(t)
    ids = [t["id"] for t in opciones]
    if len(set(ids)) != len(ids):
        raise ValueError("IDs duplicados en los temas vigentes")
    return opciones


def seleccionado(identificador, formato):
    temas = cargar_elegibles()
    usados = {x.get("tema_id") for x in cargar_historial()
              if x.get("estado") in ("subido", "publicado")}
    if identificador:
        candidatos = [x for x in temas if x["id"] == identificador]
        if not candidatos:
            raise ValueError("El tema indicado no es válido, existe o está caducado")
        if identificador in usados and os.environ.get("PERMITIR_REPETIR_TEMA") != "SI":
            raise ValueError("Tema ya subido: se impide duplicar publicaciones")
    else:
        candidatos = [x for x in temas if x["id"] not in usados]
    if formato == "largo":
        candidatos = [x for x in candidatos
                      if isinstance(x.get("guion_largo"), str)
                      and len(x["guion_largo"].split()) >= 650]
    if not candidatos:
        raise ValueError("No quedan temas verificables aptos para este formato. "
                         "Añade temas nuevos antes de producir más vídeos.")
    return sorted(candidatos,
                  key=lambda t: (-int(t.get("prioridad", 0)), t["id"]))[0]


def preparar_plan(t, formato):
    texto, descripcion, plan = preparar(t)
    if formato == "largo":
        # El guion largo se escribe y revisa manualmente: la IA no lo rellena.
        texto = re.sub(r"\s+", " ", t["guion_largo"]).strip()
        escenas = t.get("escenas_largas")
        if not isinstance(escenas, list) or len(escenas) < 8:
            raise ValueError("Un largo exige al menos 8 escenas_largas verificadas")
        if any(not isinstance(s, str) or len(s.split()) < 20 for s in escenas):
            raise ValueError("Cada escena larga debe tener al menos 20 palabras")
        # Se narra el texto de las escenas, en el mismo orden que lo visual.
        texto = " ".join(s.strip() for s in escenas)
        if len(texto.split()) < 650:
            raise ValueError("El guion narrado de largo requiere 650 palabras")
        plan["escenas"] = [{"tipo":"hecho_verificado", "texto":s} for s in escenas]
        plan["duracion_objetivo_segundos"] = [240, 900]
    if formato == "short":
        # Mantener correspondencia exacta entre cada escena y su narración.
        texto = " ".join(s["texto"].strip() for s in plan["escenas"])
    plan["formato"] = formato
    plan["tema_id"] = t["id"]
    plan["titulo_propuesto"] = t["titulo"][:95]
    plan["huella_guion"] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    plan["revision_pendiente"] = True
    plan["publicacion_automatica"] = False
    descripcion += "\nIdentificador editorial: CG-ID:" + t["id"] + "\n"
    return texto, descripcion, plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", default="")
    ap.add_argument("--formato", choices=("short", "largo"), default="short")
    args = ap.parse_args()
    t = seleccionado(args.tema.strip(), args.formato)
    texto, descripcion, plan = preparar_plan(t, args.formato)
    SALIDA.mkdir(exist_ok=True)
    (SALIDA/"guion.txt").write_text(texto+"\n", encoding="utf-8")
    (SALIDA/"descripcion.txt").write_text(descripcion, encoding="utf-8")
    (SALIDA/"plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Tema seleccionado:",t["id"])
    print("Formato:",args.formato)
    print("Palabras:",len(texto.split()))
    print("Preparado para producción con revisión posterior.")


if __name__ == "__main__":
    main()
