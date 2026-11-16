"""Metadatos internos de Píxel Feroz fuera de la descripción pública.

Los identificadores que ayudan a evitar vídeos duplicados se guardan en
YouTube snippet.tags, no en la descripción. Se conserva compatibilidad con
descripciones de las primeras subidas que sí contenían marcadores antiguos.
"""
import re

FORMATO_VALIDO = frozenset(("short", "largo"))
MARCADOR_ID = "pf_id_"
MARCADOR_FORMATO = "pf_formato_"


def etiquetas_internas(tema_id, formato):
    if not isinstance(tema_id, str) or not re.fullmatch(r"[a-z0-9_-]{3,60}", tema_id):
        raise ValueError("Identificador de tema no válido")
    if formato not in FORMATO_VALIDO:
        raise ValueError("Formato no válido")
    return [MARCADOR_ID + tema_id, MARCADOR_FORMATO + formato]


def normalizar_etiquetas(etiquetas, tema_id, formato):
    if not isinstance(etiquetas, list):
        raise ValueError("Las etiquetas del plan deben ser una lista")
    publicas = [etiqueta.strip() for etiqueta in etiquetas if isinstance(etiqueta, str)
                and etiqueta.strip()
                and not etiqueta.startswith((MARCADOR_ID, MARCADOR_FORMATO))]
    final = list(dict.fromkeys(publicas + etiquetas_internas(tema_id, formato)))
    if len(final) > 30 or len(",".join(final)) > 440:
        raise ValueError("Demasiadas etiquetas para YouTube")
    return final


def es_duplicado(snippet, tema_id, formato):
    """Compara tags nuevos y marcadores históricos de los vídeos existentes."""
    tags = snippet.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    identificador, etiqueta_formato = etiquetas_internas(tema_id, formato)
    if identificador in tags:
        formatos = {tag for tag in tags if tag.startswith(MARCADOR_FORMATO)}
        # Si existe ID sin formato, bloqueamos por seguridad.
        if etiqueta_formato in formatos or not formatos:
            return True

    descripcion = snippet.get("description", "")
    lineas = descripcion.splitlines() if isinstance(descripcion, str) else []
    legado_id = "Identificador editorial: PF-ID:" + tema_id
    legado_formato = "Formato editorial: PF-FORMATO:" + formato
    if legado_id in lineas:
        if legado_formato in lineas:
            return True
        # Primera generación de Shorts sin identificador de formato.
        if formato == "short" and not any(
            l.startswith("Formato editorial: PF-FORMATO:") for l in lineas
        ):
            return True
    return False


def limpiar_marcadores_anteriores(descripcion):
    """Limpia descripciones antiguas conservando texto y fuentes intactos."""
    lineas = descripcion.splitlines()
    lineas = [
        l for l in lineas
        if not l.startswith("Identificador editorial: PF-ID:")
        and not l.startswith("Formato editorial: PF-FORMATO:")
    ]
    return "\n".join(lineas).strip()
