#!/usr/bin/env python3
"""Prepara AHORA una cola editorial de GTA VI sin producir vídeos ni publicar.

El repo es público: solo exporta borradores basados en noticias OFICIALES
ya publicadas. Las ideas sobre gameplay todavía no demostrado se bloquean.
"""
import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from editorial import preparar_plan, cargar_historial
from preparar_contenido import validar_tema
from experimentos_portadas import generar as crear_ab

BASE = Path(__file__).resolve().parent
CALENDARIO = BASE / "calendario_publicacion.json"
TEMAS = BASE / "temas_verificados.json"
IDEAS = BASE / "ideas_postlanzamiento.json"
DESTINO = BASE / "salida" / "lanzamiento"


def comprobar_calendario(calendario, temas, ideas):
    if calendario.get("timezone") != "Europe/Madrid":
        raise ValueError("La agenda debe ser para la hora peninsular española")
    if calendario.get("lanzamiento_previsto") != "2026-11-19T00:00:00+01:00":
        raise ValueError("Revisar la fecha oficial de lanzamiento antes de seguir")
    ids = set()
    for slot in calendario["slots"]:
        if slot["id"] in ids:
            raise ValueError("Slot de calendario duplicado")
        ids.add(slot["id"])
        if slot["formato"] not in ("short", "largo"):
            raise ValueError("Formato no permitido")
        dia = date.fromisoformat(slot["fecha"])
        if not "2026-11-18" <= dia.isoformat() <= "2026-11-22":
            raise ValueError("Slot fuera del especial")
        if slot["publicar_automaticamente"] is not False or slot["subir_siempre_privado"] is not True:
            raise ValueError("Prohibido programar publicación pública automática")
        tema = slot.get("tema_confirmado_reserva")
        idea = slot.get("idea_postlanzamiento")
        if (idea and idea not in ideas) or (not tema and idea not in ideas):
            raise ValueError("Idea sin plantilla de verificación")
        if tema:
            if tema not in temas:
                raise ValueError("Tema reservado inexistente")
            if slot["formato"] not in temas[tema].get("formatos", ["short"]):
                raise ValueError("Tema no apto para ese formato")
            vence = temas[tema].get("vigente_hasta")
            if vence and dia > date.fromisoformat(vence):
                raise ValueError("Tema caducará antes del slot")
    return True


def preparar(archivo_calendario=CALENDARIO, destino=DESTINO):
    calendario = json.loads(Path(archivo_calendario).read_text(encoding="utf-8"))
    temas_lista = json.loads(TEMAS.read_text(encoding="utf-8"))
    temas = {
        x["id"]: validar_tema(x) for x in temas_lista
        if x["estado"] == "confirmado"
        and (
            not x.get("vigente_hasta")
            or date.fromisoformat(x["vigente_hasta"]) >= date.today()
        )
    }
    ideas_lista = json.loads(IDEAS.read_text(encoding="utf-8"))["ideas"]
    ideas = {x["id"]: x for x in ideas_lista}
    comprobar_calendario(calendario, temas, ideas)
    usados = {
        (x["tema_id"], x.get("formato", "short"))
        for x in cargar_historial()
        if x.get("estado") in ("subido", "publicado")
    }
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    orden = []
    creados = set()
    for slot in calendario["slots"]:
        formato = slot["formato"]
        tema_id = slot.get("tema_confirmado_reserva")
        clave = (tema_id, formato)
        estado = ("pendiente_verificacion_postlanzamiento"
                  if not tema_id else "ya_subido_privado"
                  if clave in usados else "lista_preparacion")
        if tema_id and clave in creados:
            estado = "reserva_repetida"
        if estado == "lista_preparacion":
            tema = temas[tema_id]
            texto, desc, plan = preparar_plan(tema, formato)
            carpeta = destino / "borradores" / (tema_id + "_" + formato)
            carpeta.mkdir(parents=True, exist_ok=True)
            (carpeta / "plan.json").write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            (carpeta / "descripcion.txt").write_text(desc, encoding="utf-8")
            if formato == "short":
                (carpeta / "guion_corto.txt").write_text(texto + "\n", encoding="utf-8")
            else:
                (carpeta / "esquema_no_narrado.txt").write_text(
                    "\n".join(tema["esquema_largo"]) + "\n", encoding="utf-8"
                )
                crear_ab(plan, tema, carpeta / "opciones_ab")
            creados.add(clave)
        orden.append({**slot, "estado_preparacion": estado,
                      "reserva":tema_id, "verificar_idea": slot["idea_postlanzamiento"]})
    (destino / "agenda.json").write_text(
        json.dumps(orden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    faltan = [x for x in orden if x["estado_preparacion"] == "pendiente_verificacion_postlanzamiento"]
    (destino / "pendientes_verificacion.json").write_text(
        json.dumps(faltan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    estados = Counter(x["estado_preparacion"] for x in orden)
    lineas = [
        "# Píxel Feroz — agenda de publicación MANUAL (hora de España)",
        "",
        "Fecha oficial anunciada de GTA VI: **19/11/2026, medianoche local**.",
        "**ATENCIÓN:** los horarios son objetivos editoriales, NUNCA publicación automática.",
        "Todos los vídeos se suben **privados** y necesitan revisión humana.",
        "Un vídeo largo con Ryan tardó cerca de **89 minutos** en CPU; "
        "tener un borrador NO significa tener MP4 listo.",
        "",
        "| Día | Hora | Formato | Reserva verificada | Idea alternativa | Estado |",
        "|---|---|---|---|---|---|",
    ]
    for s in orden:
        lineas.append(
            f"| {s['fecha']} | {s['hora']} | {s['formato']} | "
            f"{s['reserva'] or '—'} | {s.get('idea_postlanzamiento') or '—'} | "
            f"{s['estado_preparacion']} |"
        )
    lineas += [
        "", "## Resumen",
        *[f"- {k}: {v}" for k,v in sorted(estados.items())],
        "",
        "## Seguridad editorial",
        "Las ideas postlanzamiento NO pueden narrarse ni presentarse como hechos hasta tener",
        "fuentes oficiales posteriores al estreno o pruebas propias autorizadas.",
        "Los borradores de este paquete se basan solo en fuentes públicas.",
        "Las miniaturas son diseños originales con Pillow, no capturas de Rockstar.",
        "Los títulos y miniaturas A/B se probarán manualmente al publicar un vídeo largo.",
        "No existe A/B oficial para Shorts ni para vídeos todavía privados.",
    ]
    (destino / "agenda.md").write_text("\n".join(lineas)+"\n", encoding="utf-8")
    print("Agenda preparada:", len(orden), "slots; estados:", dict(estados))
    print("Borradores de texto y portadas aprobables disponibles en el artifact.")
    print("CERO vídeos públicos, CERO vídeos subidos y CERO hechos inventados.")
    return orden


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path, default=DESTINO)
    args = ap.parse_args()
    preparar(destino=args.salida)


if __name__ == "__main__":
    main()
