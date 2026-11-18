"""Paquete visual gaming-news original, sin imágenes de juegos de terceros.

Los fondos son gráficos editoriales abstractos, NO gameplay ni imágenes
atribuibles a Rockstar. Pensado para render automatizado con PIL + FFmpeg.
"""
import hashlib
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw
from generar_short import fuente, partir_lineas

W, H = 720, 1280
CIAN, ROSA, BLANCO = (52, 237, 227), (255, 69, 152), (244, 248, 252)
ETIQUETAS = {
    "gancho": "ÚLTIMA HORA",
    "contexto": "EL CONTEXTO",
    "hecho_verificado": "DATO VERIFICADO",
    "cierre": "LA CLAVE",
}

def palabras_destacadas(texto):
    palabras = texto.replace("¿", "").replace("¡", "").split()
    significativas = [p.strip(".,:;!?") for p in palabras if len(p.strip(".,:;!?")) >= 4]
    return " ".join(significativas[:4] or palabras[:3]).upper()[:35]

def tarjeta_gaming(escena, indice, total, titulo, destino):
    """Escena vertical con jerarquía clara y gráficos, evitando ciudades falsas."""
    texto = " ".join(escena["texto"].split())
    if not texto:
        raise ValueError("No se admite una escena sin texto")
    seed = int(hashlib.sha256((texto + str(indice)).encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    imagen = Image.new("RGB", (W, H), (8, 13, 27))
    d = ImageDraw.Draw(imagen)
    # Paneles editoriales, retícula, diagonales y líneas de seguimiento.
    acento = ROSA if indice % 3 == 0 else CIAN
    for y in range(H):
        k = y / H
        d.line((0,y,W,y), fill=(int(8+12*k),int(13+9*k),int(27+20*k)))
    for x in range(-200, 1100, 95):
        d.line((x, 0, x-245, H), fill=(23, 35, 58), width=2)
    for y in range(175, H, 95):
        d.line((0, y, W, y), fill=(17, 29, 48), width=2)
    # Motivos de radar y diagrama de conexiones: abstractos e inequívocos.
    cx, cy = (490, 410) if indice % 2 else (200, 370)
    for radius in (100, 165, 230, 305):
        d.arc((cx-radius,cy-radius,cx+radius,cy+radius),
              start=190+indice*13,end=460+indice*13,fill=(38,75,91),width=4)
    nodos = [(rng.randint(70,645),rng.randint(255,750)) for _ in range(9)]
    for a,b in zip(nodos,nodos[1:]):
        d.line((a[0],a[1],b[0],b[1]),fill=(43,94,111),width=3)
    for x,y in nodos:
        d.ellipse((x-7,y-7,x+7,y+7),fill=acento)
    d.polygon([(0,725),(W,615),(W,1080),(0,1190)],fill=(8,17,33))
    d.polygon([(0,820),(W,705),(W,755),(0,870)],fill=acento)
    d.rectangle((0,0,W,15),fill=acento)
    d.rounded_rectangle((34,50,686,130), radius=17,fill=(11,28,46))
    d.text((55,68),"PÍXEL FEROZ",font=fuente(35,True),fill=BLANCO)
    d.rounded_rectangle((34,154,373,206),radius=12,fill=acento)
    d.text((49,166),ETIQUETAS.get(escena["tipo"],"GAMING NEWS"),
           font=fuente(21,True),fill=(8,17,30))
    # Gran titular: solo un extracto, no repetir una pared de texto.
    destacado = palabras_destacadas(texto)
    for size in range(66,31,-2):
        f = fuente(size,True)
        lineas = partir_lineas(d,destacado,f,600)
        if len(lineas) <= 3 and len(lineas)*int(size*1.24) <= 245:
            break
    y0 = 840
    for linea in lineas[:3]:
        d.text((43,y0),linea,font=f,fill=BLANCO,
               stroke_width=1,stroke_fill=(0,0,0))
        y0 += int(size*1.24)
    # Segundo bloque complementario breve.
    palabras = texto.split()
    subtitulo = " ".join(palabras[4:14])
    if subtitulo:
        f2 = fuente(24,False)
        for k,linea in enumerate(partir_lineas(d,subtitulo,f2,620)[:3]):
            d.text((45,1080+k*35),linea,font=f2,fill=(195,218,229))
    d.rectangle((34,1200,686,1208),fill=(37,61,78))
    d.rectangle((34,1200,34+int(652*(indice+1)/max(1,total)),1208),fill=acento)
    d.text((38,1223),f"NOTICIAS DE VIDEOJUEGOS  ·  {indice+1:02d}/{total:02d}",
           font=fuente(17,True),fill=(173,199,216))
    destino = Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    imagen.save(destino,optimize=True)
