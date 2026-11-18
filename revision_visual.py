"""Exporta mosaico y fotogramas individuales para revisar Shorts desde GitHub.

Solo incluye pantallas y fotografías oficiales seleccionadas; no exporta MP4,
audio ni guion completo al repositorio público.
"""
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from generar_short import fuente

def exportar_revision(salida, escenas, catalogo=None):
    destino = Path(salida) / "revision_visual"
    destino.mkdir(parents=True, exist_ok=True)
    dir_escenas = destino / "escenas"
    dir_fuentes = destino / "imagenes_originales_seleccionadas"
    dir_escenas.mkdir(exist_ok=True)
    dir_fuentes.mkdir(exist_ok=True)
    columnas, tam_w, tam_h = 4, 225, 430
    filas = (len(escenas) + columnas - 1) // columnas
    mosaico = Image.new("RGB", (columnas*tam_w, max(1,filas)*tam_h), (7,16,28))
    dibujo = ImageDraw.Draw(mosaico)
    salida_json = []
    for i, escena in enumerate(escenas):
        imagen = Path(escena["pantalla"])
        with Image.open(imagen) as im:
            frame = im.convert("RGB")
            thumb = ImageOps.contain(frame, (tam_w-8,tam_h-48))
        x = i % columnas * tam_w
        y = i // columnas * tam_h
        mosaico.paste(thumb, (x+(tam_w-thumb.width)//2,y+4))
        dibujo.text((x+12,y+tam_h-38),f'{i+1:02d} | {escena["medio"]}',
                     font=fuente(18,True),fill=(228,244,249))
        guardada = dir_escenas / f"escena_{i+1:02d}.jpg"
        frame.thumbnail((540,960),Image.Resampling.LANCZOS)
        frame.save(guardada, quality=82, optimize=True)
        dato = {
            "escena": i+1,
            "tipo": escena["medio"],
            "preview": str(guardada.relative_to(destino)),
        }
        if escena.get("foto"):
            origen = Path(escena["foto"])
            copia = dir_fuentes / (f'{i+1:02d}_'+origen.name)
            shutil.copyfile(origen, copia)
            dato["imagen_usada"] = str(copia.relative_to(destino))
            dato["sha256"] = hashlib.sha256(copia.read_bytes()).hexdigest()
            dato["credito"] = escena.get("credito","")
            dato["titulo"] = escena.get("titulo", origen.stem)
        salida_json.append(dato)
    mosaico.save(destino/"mosaico_escenas.jpg",quality=89)
    (destino/"manifiesto_escenas.json").write_text(json.dumps({
        "origen": "Rockstar Games — GTA VI Media" if catalogo else "Recursos editoriales",
        "fuente": "https://www.rockstargames.com/VI/media/screenshots" if catalogo else "",
        "nota": "Crédito no equivale a licencia comercial. Revisar derechos antes de publicar.",
        "escenas": salida_json,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Revisión visual exportada:",len(salida_json),"escenas",flush=True)

def anadir_fuente_descripcion(archivo, incluir_clips=False):
    path=Path(archivo)
    texto=path.read_text(encoding="utf-8")
    marca="Material visual: capturas oficiales de Grand Theft Auto VI"
    marca_clips="Clips oficiales: Rockstar Games / Take-Two Interactive."
    if marca in texto and (not incluir_clips or marca_clips in texto):
        return
    bloque=("")
    if marca not in texto:
        bloque=("\n\n"+marca+
                "\nCréditos de las imágenes: Rockstar Games / Take-Two Interactive."+
                "\nFuente oficial: https://www.rockstargames.com/VI/media/screenshots"+
                "\nSe incluyen imágenes para ilustrar un comentario editorial; "+
                "la atribución no supone una licencia comercial.\n")
    if incluir_clips and marca_clips not in texto:
        bloque+=("\n"+marca_clips+
                 "\nFuente de los clips: https://www.rockstargames.com/VI/media/videos"+
                 "\nEl audio oficial de los clips no se utiliza en este montaje.\n")
    # La descripción de YouTube limita a 5000 caracteres (upload usa 4800).
    if len(texto)+len(bloque) > 4800:
        raise RuntimeError("Descripción demasiado larga para añadir los créditos oficiales")
    path.write_text(texto.rstrip()+"\n"+bloque,encoding="utf-8")
