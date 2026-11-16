#!/usr/bin/env python3
"""Primer prototipo de Short vertical con visuales originales y voz Piper.

Sin subida a YouTube. El material generado requiere revision editorial.
Requisitos: pillow, piper (piper-tts), ffmpeg y ffprobe.
"""
import argparse
import json
import math
import random
import shutil
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "salida"
TRABAJO = SALIDA / "render"
VOZ = RAIZ / "voz"
ANCHO, ALTO, FPS = 720, 1280, 20
ACENTO = (42, 230, 218)
ROSA = (255, 85, 160)
URL_MODELO = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx"
)
FUENTE_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FUENTE_NEGRITA = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ejecutar(args, **kwargs):
    print("Ejecutando:", args[0], flush=True)
    subprocess.run(args, check=True, **kwargs)


def fuente(tam, negrita=False):
    ruta = FUENTE_NEGRITA if negrita else FUENTE_NORMAL
    if not Path(ruta).is_file():
        raise RuntimeError("Falta la fuente DejaVu Sans: " + ruta)
    return ImageFont.truetype(ruta, tam)


def partir_lineas(dibujo, texto, fnt, ancho_max):
    resultado = []
    for parrafo in texto.split("\n"):
        linea = ""
        for palabra in parrafo.split():
            propuesta = (linea + " " + palabra).strip()
            if dibujo.textbbox((0, 0), propuesta, font=fnt)[2] <= ancho_max:
                linea = propuesta
            else:
                if linea:
                    resultado.append(linea)
                    linea = palabra
                else:
                    # El contenido extenso se divide en bloques cortos.
                    fragmento = ""
                    for letra in palabra:
                        intento = fragmento + letra
                        if dibujo.textbbox((0, 0), intento, font=fnt)[2] > ancho_max and fragmento:
                            resultado.append(fragmento)
                            fragmento = letra
                        else:
                            fragmento = intento
                    linea = fragmento
        if linea:
            resultado.append(linea)
    return resultado


def tarjeta_escena(escena, indice, total, titulo, destino):
    imagen = Image.new("RGB", (ANCHO, ALTO))
    dibujo = ImageDraw.Draw(imagen)
    for y in range(ALTO):
        k = y / ALTO
        dibujo.line((0, y, ANCHO, y), fill=(
            int(6 + 9 * k), int(13 + 9 * k), int(29 + 19 * k)
        ))
    azar = random.Random(90210 + indice)
    # Ciudad original de geometria vectorial: no utiliza capturas de juegos.
    for x in range(-12, ANCHO + 20, 37):
        h = azar.randint(75, 260)
        dibujo.rectangle((x, 1030 - h, x + 27, 1180), fill=(19, 37, 64))
        for yy in range(1050 - h, 1160, 23):
            if azar.random() > .45:
                dibujo.rectangle((x+7, yy, x+12, yy+8), fill=(35, 93, 105))
    dibujo.polygon([(0, 1150), (ANCHO, 1080), (ANCHO, ALTO), (0, ALTO)], fill=(10, 20, 36))
    dibujo.rounded_rectangle((40, 45, ANCHO-40, 112), radius=22, fill=(15, 39, 61))
    dibujo.text((62, 58), "PÍXEL FEROZ", font=fuente(28, True), fill=ACENTO)
    dibujo.line((48, 136, ANCHO-48, 136), fill=ROSA, width=5)

    etiqueta = {
        "gancho": "ATENCIÓN",
        "contexto": "CONTEXTO",
        "hecho_verificado": "DATO CONFIRMADO",
        "cierre": "RESUMEN",
    }.get(escena["tipo"], "DATO")
    f_etiqueta = fuente(25, True)
    dibujo.text((54, 220), etiqueta, font=f_etiqueta, fill=ROSA)
    dibujo.rounded_rectangle((40, 292, ANCHO-40, 883), radius=34, fill=(19, 30, 53))
    dibujo.rounded_rectangle((44, 297, ANCHO-44, 881), radius=30, outline=(53, 91, 108), width=3)

    texto = escena["texto"].strip()
    area = ANCHO - 120
    for tam in range(43, 25, -2):
        f = fuente(tam, True)
        lineas = partir_lineas(dibujo, texto, f, area)
        interlineado = int(tam * 1.38)
        if len(lineas) * interlineado < 510:
            break
    if len(lineas) * interlineado >= 510:
        raise ValueError("Texto demasiado largo para escena: " + str(indice))
    y0 = 575 - len(lineas) * interlineado / 2
    for j, linea in enumerate(lineas):
        dibujo.text((65, int(y0 + j * interlineado)), linea, font=f, fill=(250, 252, 255))

    dibujo.text((52, 932), titulo[:42], font=fuente(20), fill=(190, 211, 228))
    dibujo.text((52, 966), "Fuentes oficiales en la descripción", font=fuente(17), fill=(134, 171, 183))
    ancho_barra = ANCHO - 96
    dibujo.rounded_rectangle((48, 1210, ANCHO-48, 1219), radius=4, fill=(48, 70, 92))
    dibujo.rounded_rectangle((48, 1210, 48 + int(ancho_barra*(indice+1)/total), 1219), radius=4, fill=ACENTO)
    dibujo.text((50, 1237), f"{indice+1:02d} / {total:02d}", font=fuente(19), fill=(199, 226, 236))
    destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(destino, optimize=True)


def descargar(si_falta, url):
    if si_falta.exists() and si_falta.stat().st_size > 5000:
        return
    si_falta.parent.mkdir(parents=True, exist_ok=True)
    temporal = si_falta.with_name(si_falta.name + ".part")
    print("Descargando voz:", si_falta.name, flush=True)
    try:
        with urllib.request.urlopen(url, timeout=90) as r, temporal.open("wb") as o:
            shutil.copyfileobj(r, o)
        temporal.replace(si_falta)
    finally:
        temporal.unlink(missing_ok=True)


def voz_piper(guion):
    for comando in ("piper", "ffmpeg"):
        if not shutil.which(comando):
            raise RuntimeError("No se encuentra el comando: " + comando)
    modelo = VOZ / "es_ES-sharvard-medium.onnx"
    descargar(modelo, URL_MODELO)
    descargar(VOZ / "es_ES-sharvard-medium.onnx.json", URL_MODELO + ".json")
    wav = SALIDA / "narracion.wav"
    ejecutar(
        ["piper", "--model", str(modelo), "--output_file", str(wav)],
        input=guion, text=True, timeout=300
    )
    with wave.open(str(wav), "rb") as w:
        segundos = w.getnframes() / w.getframerate()
    if not (5 <= segundos <= 120):
        raise ValueError(f"Duración de voz inesperada: {segundos:.1f} s")
    print(f"Narración: {segundos:.1f} segundos", flush=True)
    return wav, segundos


def producir_video(plan, wav, segundos):
    escenas = plan["escenas"]
    if not 2 <= len(escenas) <= 12:
        raise ValueError("Cantidad de escenas no válida")
    TRABAJO.mkdir(parents=True, exist_ok=True)
    titulo = plan["titulo_propuesto"]
    pesos = [max(4, len(s["texto"].split())) for s in escenas]
    fotogramas = round(segundos * FPS)
    reparto = [max(1, round(fotogramas * p / sum(pesos))) for p in pesos]
    reparto[-1] += fotogramas - sum(reparto)
    if min(reparto) < 1:
        raise ValueError("Escenas demasiado numerosas para la narración")
    clips = []
    for i, (escena, nframes) in enumerate(zip(escenas, reparto)):
        imagen = TRABAJO / f"escena_{i:02d}.png"
        clip = TRABAJO / f"clip_{i:02d}.mp4"
        tarjeta_escena(escena, i, len(escenas), titulo, imagen)
        ejecutar([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", str(imagen),
            "-frames:v", str(nframes), "-c:v", "libx264",
            "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
            "-r", str(FPS), str(clip)
        ], timeout=240)
        clips.append(clip)
    lista = TRABAJO / "lista.txt"
    lista.write_text("".join(f"file '{clip.name}'\n" for clip in clips), encoding="utf-8")
    video = SALIDA / "pixel_feroz_short.mp4"
    ejecutar([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "concat", "-safe", "0", "-i", str(lista),
        "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", str(video)
    ], timeout=240)
    if video.stat().st_size < 20000:
        raise RuntimeError("El MP4 generado está vacío o incompleto")
    print("MP4 generado:", video, "bytes:", video.stat().st_size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=SALIDA / "plan.json")
    parser.add_argument("--guion", type=Path, default=SALIDA / "guion.txt")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if plan.get("estado") != "BORRADOR_PENDIENTE_REVISION":
        raise ValueError("Se requiere un borrador editorial válido")
    if plan.get("publicacion_automatica") is not False:
        raise ValueError("La publicación automática debe estar desactivada")
    guion = args.guion.read_text(encoding="utf-8").strip()
    if not guion:
        raise ValueError("Guion vacío")
    wav, duracion = voz_piper(guion)
    producir_video(plan, wav, duracion)
    print("REVISIÓN MANUAL NECESARIA. No se ha subido nada a YouTube.")


if __name__ == "__main__":
    main()
