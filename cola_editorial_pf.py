"""Colas de producción independientes para Píxel Feroz (PF-90).

Cada formato tiene su propia lista ordenada de IDs confirmados y vigentes.
Los temas no verificados se conservan aparte y NO se producen automáticamente.
Nunca se retira un tema por un fallo de render, TTS o descarga.
"""
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent

def ruta(formato, base=None):
    if formato not in ("short", "largo"):
        raise ValueError("Formato de cola desconocido")
    return (Path(base) if base is not None else BASE) / "colas" / (
        "shorts.json" if formato == "short" else "documentales.json"
    )

def cargar(formato, base=None):
    path = ruta(formato, base)
    if not path.is_file():
        return None
    datos = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(datos, list) or any(not isinstance(x, str) or not x for x in datos):
        raise ValueError("La cola de producción debe ser una lista de IDs")
    if len(set(datos)) != len(datos):
        raise ValueError("La cola de producción contiene IDs repetidos")
    return datos

def ordenar(candidatos, formato, base=None):
    cola = cargar(formato, base)
    if cola is None:
        return candidatos
    por_id = {t["id"]: t for t in candidatos}
    # Una cola vacía no vuelve a los temas antiguos: se agota explícitamente.
    return [por_id[tema_id] for tema_id in cola if tema_id in por_id]

def retirar(formato, tema_id, base=None):
    path = ruta(formato, base)
    cola = cargar(formato, base)
    if cola is None or tema_id not in cola:
        return False
    temporal = path.with_suffix(path.suffix + ".tmp")
    temporal.write_text(
        json.dumps([x for x in cola if x != tema_id],
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporal, path)
    return True

def verificar_cobertura(formato, catalogo, historial, base=None):
    usados = {x.get("tema_id") for x in historial
              if x.get("formato", "short") == formato and x.get("estado") in ("subido", "publicado")}
    elegibles = {x["id"] for x in catalogo if formato in x.get("formatos", ["short"])
                 and x.get("estado") == "confirmado"}
    cola = cargar(formato, base)
    lista = cola if cola is not None else list(elegibles)
    return {"formato": formato, "pendientes":len([x for x in lista if x in elegibles and x not in usados])}
