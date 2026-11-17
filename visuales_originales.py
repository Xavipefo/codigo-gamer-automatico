"""Fondos editoriales originales creados localmente. NO son imágenes de GTA VI."""
import hashlib
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

CREDITO = "Ilustración original del canal (no es gameplay)"

def crear_banco_original(tema_id, directorio, cantidad=6):
    """Genera panoramas originales sin red, modelos ni archivos de terceros."""
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    seed = int(hashlib.sha256(tema_id.encode("utf-8")).hexdigest()[:12], 16)
    resultado = []
    for indice in range(cantidad):
        rng = random.Random(seed + 7919 * indice)
        w, h = 1280, 720
        paletas = [
            ((7, 22, 58), (238, 92, 135), (255, 194, 111)),
            ((7, 26, 48), (62, 142, 193), (254, 165, 118)),
            ((20, 19, 50), (154, 75, 136), (250, 172, 94)),
            ((6, 30, 45), (38, 150, 152), (244, 184, 116)),
            ((17, 24, 56), (98, 112, 178), (232, 138, 113)),
            ((9, 19, 39), (177, 70, 119), (252, 186, 132)),
        ]
        arriba, abajo, sol = paletas[indice % len(paletas)]
        im = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(im)
        horizonte = 475 + rng.randint(-30, 30)
        for y in range(h):
            t = min(1, y / float(horizonte))
            color = tuple(int(a * (1-t) + b * t) for a, b in zip(arriba, abajo))
            d.line((0, y, w, y), fill=color)
        sx = 170 + (indice * 167) % 880
        sy = 225 + (indice * 29) % 140
        d.ellipse((sx-78, sy-78, sx+78, sy+78), fill=sol)
        d.rectangle((0, horizonte-7, w, horizonte+14), fill=(34, 54, 71))
        # Dos planos urbanos y ventanas: detalles únicos en cada lámina.
        for plano in range(2):
            x = -40
            while x < w:
                ancho = rng.randint(48, 125) if plano == 0 else rng.randint(65, 150)
                alto = rng.randint(85, 270) if plano == 0 else rng.randint(110, 330)
                base = horizonte + (20 if plano == 0 else 85)
                tono = (24, 41, 65) if plano == 0 else (11, 26, 48)
                d.rectangle((x, base-alto, x+ancho, base+40), fill=tono)
                for wx in range(x+13, x+ancho-8, 18):
                    for wy in range(base-alto+18, base-14, 26):
                        if rng.random() < .38:
                            d.rectangle((wx, wy, wx+5, wy+9),
                                        fill=(210, 158, 115) if plano == 0 else (82, 172, 174))
                x += ancho + rng.randint(4, 16)
        # Carretera en perspectiva, con marcas viales.
        d.polygon([(0,h),(w,h),(740,horizonte+95),(540,horizonte+95)], fill=(17, 28, 45))
        for z in range(5):
            y0 = horizonte + 103 + z*z*8
            span = 2 + z*3
            d.polygon([(637-span,y0),(643+span,y0),
                       (650+span*2,y0+6+z*2),(629-span*2,y0+6+z*2)],
                      fill=(241, 187, 117))
        # Silueta de vehículo ficticio ilustrada, no un modelo real.
        if indice % 3 != 2:
            cx = 350 + (indice*137) % 520
            cy = 590 + (indice % 2)*37
            d.rounded_rectangle((cx-165, cy-38, cx+165, cy+36), radius=18,
                                fill=(42+indice*10, 122, 155))
            d.polygon([(cx-95, cy-38),(cx-55,cy-92),
                       (cx+65,cy-92),(cx+112,cy-38)],fill=(32, 49, 75))
            d.polygon([(cx-49,cy-83),(cx+58,cy-83),
                       (cx+88,cy-41),(cx-77,cy-41)],fill=(92, 151, 170))
            for xx in (cx-105,cx+105):
                d.ellipse((xx-30,cy+14,xx+30,cy+74),fill=(8,16,31))
                d.ellipse((xx-14,cy+30,xx+14,cy+59),fill=(95,121,139))
        # Ornamento editorial y etiqueta visible para evitar confusiones.
        d.rounded_rectangle((34,32,315,75), radius=12, fill=(7,20,34))
        d.text((49,45), "PIXEL FEROZ | ARTE ORIGINAL", fill=(236,244,249))
        d.rounded_rectangle((30,h-60,375,h-21),radius=9,fill=(6,19,35))
        d.text((45,h-49),"ILUSTRACION · NO ES GAMEPLAY",fill=(230,235,241))
        ruta = directorio / f"editorial_original_{indice:02d}.jpg"
        im.save(ruta, quality=88, optimize=True)
        resultado.append((ruta, CREDITO))
    return resultado
