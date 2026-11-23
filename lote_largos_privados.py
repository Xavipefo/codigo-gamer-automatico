#!/usr/bin/env python3
"""PF-43: solicitar de 1 a 3 documentales largos verificados en PRIVADO.

La planificación se hace sobre main y reserva cada tema antes de
iniciar workflows individuales, que respetan su propia concurrencia.
Nunca hace públicos los vídeos.
"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ=Path(__file__).resolve().parent
EXPIRACION=timedelta(hours=72)


def leer(path):
    datos=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(datos,list):
        raise ValueError("Se requiere una lista JSON")
    return datos


def planificar(cantidad,temas="",raiz=RAIZ,ahora=None):
    from preparar_contenido import validar_tema
    raiz=Path(raiz)
    ahora=ahora or datetime.now(timezone.utc)
    if not isinstance(cantidad,int) or not 1<=cantidad<=3:
        raise ValueError("Un lote admite de 1 a 3 documentales")
    catalogo=leer(raiz/"temas_verificados.json")
    historial=leer(raiz/"historial_publicados.json")
    ruta=raiz/"reservas_largos.json"
    reservas=leer(ruta) if ruta.exists() else []
    ids=set()
    disponibles=[]
    usados={(x.get("tema_id"),x.get("formato")) for x in historial
            if isinstance(x,dict) and x.get("estado") in ("subido","publicado")}
    activas=[]
    for r in reservas:
        try:
            t=datetime.fromisoformat(r["creado_utc"].replace("Z","+00:00"))
            if t.tzinfo and timedelta(0)<=ahora-t<EXPIRACION:
                activas.append(r)
        except (KeyError,ValueError,TypeError):
            continue
    apartados={x.get("tema_id") for x in activas}
    for tema in catalogo:
        ident=tema.get("id") if isinstance(tema,dict) else None
        if not isinstance(ident,str) or ident in ids:
            raise ValueError("ID no válido o repetido en catálogo")
        ids.add(ident)
        if "largo" not in tema.get("formatos",["short"]):
            continue
        if tema.get("estado")!="confirmado":
            continue
        # Comprobar el estado vigente ANTES de ponerlo en cola.
        try:
            validar_tema(tema)
        except ValueError:
            continue
        if (ident,"largo") in usados or ident in apartados:
            continue
        disponibles.append(ident)
    # PF-90: lote ordenado por cola específica de documentales.
    from cola_editorial_pf import cargar as cargar_cola
    orden = cargar_cola("largo", base=raiz)
    if orden is not None:
        elegibles = set(disponibles)
        disponibles = [x for x in orden if x in elegibles]
    if temas.strip():
        elegidos=[x.strip() for x in temas.split("|")]
        if (len(elegidos)!=cantidad or len(set(elegidos))!=cantidad or
            any(x not in disponibles for x in elegidos)):
            raise ValueError("IDs no disponibles, repetidos o cantidad diferente")
    else:
        elegidos=disponibles[:cantidad]
        if len(elegidos)!=cantidad:
            raise ValueError("No hay suficientes documentales nuevos para este lote")
    return {
        "temas":elegidos,"cantidad":cantidad,"privacidad":"private",
        "publicacion_publica":False,"reservas_activas":activas,
        "hora_utc":ahora.isoformat(),"rama":"main",
    }


def reservar(plan,raiz=RAIZ):
    ruta=Path(raiz)/"reservas_largos.json"
    actual=list(plan["reservas_activas"])
    for tema in plan["temas"]:
        actual.append({"tema_id":tema,"creado_utc":plan["hora_utc"],
                       "estado":"solicitado_privado"})
    ruta.write_text(json.dumps(actual,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return ruta


def lanzar(plan,runner=subprocess.run):
    if os.getenv("PF_CONFIRMACION")!="GENERAR_PRIVADO":
        raise PermissionError("Falta confirmación explícita de subida privada")
    if not os.getenv("GH_TOKEN") or not re.fullmatch(
        r"[\w.-]+/[\w.-]+",os.getenv("GH_REPO","")
    ):
        raise RuntimeError("GitHub no está autenticado")
    aceptados=[]
    for tema in plan["temas"]:
        p=runner([
            "gh","workflow","run","crear_largo_privado.yml","--ref","main",
            "-f","tema="+tema,"-f","exigir_material_real=false"
        ],capture_output=True,text=True,check=False)
        if p.returncode:
            raise RuntimeError(
                f"Solicitados {len(aceptados)}/{len(plan['temas'])}; "
                f"no repetir los primeros sin revisar Actions: {p.stderr[-300:]}"
            )
        aceptados.append(tema)
    return aceptados


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cantidad",type=int,default=1)
    parser.add_argument("--temas",default="")
    parser.add_argument("--plan",default="lote_largos_plan.json")
    parser.add_argument("--reservar",action="store_true")
    parser.add_argument("--despachar",action="store_true")
    args=parser.parse_args()
    ruta=Path(args.plan)
    if args.despachar:
        print("Solicitudes privadas:",lanzar(json.loads(ruta.read_text(encoding="utf-8"))))
        return
    plan=planificar(args.cantidad,args.temas)
    if args.reservar:
        reservar(plan)
    ruta.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Documentales reservados:",plan["temas"])


if __name__=="__main__":
    main()
