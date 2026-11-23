"""Cola de producción de Píxel Feroz.

Lee temas_verificados.json en el orden físico de sus entradas. Un historial
independiente por formato evita repetir Shorts o vídeos largos.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from preparar_contenido import preparar, validar_tema, construir_descripcion, CTA_SUSCRIPCION
from voz_produccion import elegir_voz

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
    ids = [t.get("id") for t in datos if isinstance(t, dict)]
    if len(set(ids)) != len(ids):
        raise ValueError("IDs duplicados en la cola de temas")
    temas = []
    for tema in datos:
        if not isinstance(tema, dict):
            raise ValueError("Entrada de cola que no es un objeto")
        vence = tema.get("vigente_hasta")
        if vence and date.fromisoformat(vence) < date.today():
            continue
        if tema.get("estado") != "confirmado":
            continue
        validar_tema(tema)
        temas.append(tema)
    return temas



def _cobertura_visual_exclusiva(tema, formato, banco):
    """Exige suficientes imágenes exactas antes de consumir un tema automático.

    Si el tema es concreto (por ejemplo Vice City), no sustituir con capturas
    de otras zonas. Las producciones manuales conservan su propia auditoría.
    """
    exclusivas=tema.get("categorias_visuales_exclusivas") or []
    if not exclusivas or banco is None:
        return True
    if not isinstance(exclusivas,list) or not all(isinstance(x,str) for x in exclusivas):
        raise ValueError("Categorías visuales exclusivas inválidas")
    fotos=[x for x in banco.get("imagenes",[])
           if x.get("categoria") in exclusivas]
    if formato=="short":
        _, _, plan=preparar(tema)
        escenas=len(plan.get("escenas",[]))
    else:
        # El número final de escenas largas se define más tarde.
        escenas=5
    minimo=max(5,(escenas+1)//2)
    return len({x["archivo"] for x in fotos})>=minimo


def _banco_para_preflight():
    """Solo se activa cuando ya se ha descargado y validado el banco."""
    from rockstar_media import BASE as BANCO, cargar_banco
    if not (BANCO/"catalogo.json").is_file():
        return None
    return cargar_banco()


def seleccionado(identificador, formato):
    if formato not in ("short", "largo"):
        raise ValueError("Formato incorrecto")
    usados = {
        (item.get("tema_id"), item.get("formato", "short"))
        for item in cargar_historial()
        if item.get("estado") in ("subido", "publicado")
    }
    posibles = []
    for tema in cargar_elegibles():
        if identificador and tema["id"] != identificador:
            continue
        if formato not in tema.get("formatos", ["short"]):
            continue
        if (tema["id"], formato) in usados:
            if identificador:
                raise ValueError(
                    "Ya existe una subida de este tema en el formato elegido"
                )
            continue
        posibles.append(tema)

    if not posibles:
        raise ValueError(
            "No quedan temas vigentes y no usados para "
            + formato + ". Actualiza temas_verificados.json."
        )
    # PF-90: Shorts y largos siguen colas propias sin selección aleatoria.
    # Las referencias manuales conservan el comportamiento de siempre.
    if not identificador:
        from cola_editorial_pf import ordenar
        import os
        linea=os.environ.get("PF_LINEA_EDITORIAL","general").strip().lower()
        if linea not in ("general","historia"):
            raise ValueError("Línea editorial desconocida")
        if linea=="historia" and formato!="short":
            raise ValueError("La serie Historia GTA VI solo admite Shorts")
        cola="historia" if linea=="historia" else formato
        posibles=ordenar(posibles, cola)
        if not posibles:
            raise RuntimeError("Cola de "+formato+" agotada o sin temas confirmados; "
                               "no sustituir con rumores ni contenido duplicado.")
    # Una categoría muy específica puede no disponer de suficientes capturas
    # oficiales. No detener toda la cola ni mezclar escenarios ajenos.
    if not identificador:
        banco=_banco_para_preflight()
        aptos=[]
        for tema in posibles:
            if _cobertura_visual_exclusiva(tema,formato,banco):
                aptos.append(tema)
            else:
                print("PF-46: tema reservado sin fotos suficientes:",
                      tema["id"],flush=True)
        if not aptos:
            raise RuntimeError("Ningún tema pendiente dispone de un banco visual "
                               "oficial suficiente. Revisar cola sin publicar.")
        posibles=aptos
    # Sin sorted(): se conserva el orden editorial de los temas aptos.
    return posibles[0]


def preparar_plan(tema, formato):
    texto, _, plan = preparar(tema)
    if formato == "largo":
        manual = tema.get("escenas_largas")
        if isinstance(manual, list) and len(manual) >= 8:
            if any(not isinstance(s, str) or len(s.split()) < 20 for s in manual):
                raise ValueError("Cada escena larga necesita al menos 20 palabras")
            escenas = [re.sub(r"\s+", " ", s).strip() for s in manual]
            if CTA_SUSCRIPCION not in escenas[-1]:
                escenas[-1] += " " + CTA_SUSCRIPCION
            texto = " ".join(escenas)
            if len(texto.split()) < 650:
                raise ValueError("Guion largo insuficiente")
            plan["escenas"] = [
                {"tipo": "hecho_verificado", "texto": x} for x in escenas
            ]
            plan["requiere_guion_ia"] = False
        else:
            # El generador con IA toma el esquema, las fuentes y los hechos.
            texto = ""
            plan["escenas"] = []
            plan["requiere_guion_ia"] = True
        plan["esquema_largo"] = tema.get("esquema_largo", [])
        plan["documental_profundo"] = bool(tema.get("documental_profundo"))
        plan["duracion_objetivo_segundos"] = (
            [900, 1500] if tema.get("documental_profundo") else [540, 900]
        )
    else:
        texto = " ".join(s["texto"].strip() for s in plan["escenas"])
        plan["requiere_guion_ia"] = False

    plan["formato"] = formato
    plan["narrador_voz"] = elegir_voz(formato)
    plan["narrador_sintetico"] = True
    plan["tema_id"] = tema["id"]
    plan["titulo_propuesto"] = tema["titulo"][:95]
    plan["texto_miniatura"] = tema.get("texto_miniatura", tema["titulo"])[:90]
    plan["huella_guion"] = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    plan["revision_pendiente"] = True
    plan["visuales_preferidos"] = tema.get("visuales_preferidos", [])
    plan["categorias_visuales_exclusivas"] = tema.get("categorias_visuales_exclusivas", [])
    plan["portada_categoria"] = tema.get("portada_categoria")
    plan["portada_paleta"] = tema.get("portada_paleta", "fucsia")
    plan["miniatura_opciones"] = tema.get("miniatura_opciones", [])
    plan["publicacion_objetivo"] = tema.get("publicacion_objetivo")
    plan["publicacion_manual_desde"] = tema.get("publicacion_manual_desde")
    plan["publicacion_automatica"] = False
    descripcion = construir_descripcion(tema, formato)
    return texto, descripcion, plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tema", default="")
    ap.add_argument("--formato", choices=("short", "largo"), default="short")
    args = ap.parse_args()
    t = seleccionado(args.tema.strip(), args.formato)
    texto, descripcion, plan = preparar_plan(t, args.formato)
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "guion.txt").write_text(texto + "\n", encoding="utf-8")
    (SALIDA / "descripcion.txt").write_text(descripcion, encoding="utf-8")
    (SALIDA / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print("Siguiente tema por orden:", t["id"])
    print("Formato:", args.formato)
    print("Narrador de este vídeo:", plan["narrador_voz"])
    print("Palabras iniciales:", len(texto.split()))
    print("IA necesaria para largo:", plan["requiere_guion_ia"])
    print("Subida: exclusivamente privada, pendiente de revisión posterior")


if __name__ == "__main__":
    main()
