#!/usr/bin/env python3
"""Motor: dos voces de Gemini con clips autorizados y gráficos originales.

Sin clips autorizados, mantiene tarjetas propias con un suave movimiento.
La subida sigue siendo exclusivamente privada para revisión humana.
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generar_short import tarjeta_escena, fuente, partir_lineas
from voz_produccion import NarradorGemini, estimar_consumo
from video_material import descargar_clip, overlay_clips

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
VOZ = BASE / "voz"
RES_WIDE = (1280, 720)
RES_SHORT = (720, 1280)


def comando(args, **kwargs):
    subprocess.run(args, check=True, timeout=900, **kwargs)


def fragmentar(texto, max_palabras):
    """Divide en bloques EQUILIBRADOS: nunca deja una cola de una palabra.

    Ejemplo: 101 palabras y límite 50 -> 34, 34 y 33 palabras,
    no 50, 50 y 1. Mantiene exactamente el orden y el contenido.
    """
    palabras = texto.split()
    if not palabras:
        return []
    # Respetar también el máximo de caracteres de la API de Gemini TTS.
    piezas = max(
        1,
        math.ceil(len(palabras) / max_palabras),
        math.ceil(len(" ".join(palabras)) / 1300),
    )
    while piezas <= len(palabras):
        base, resto = divmod(len(palabras), piezas)
        grupos = []
        inicio = 0
        for indice in range(piezas):
            longitud = base + (1 if indice < resto else 0)
            grupos.append(" ".join(palabras[inicio:inicio + longitud]))
            inicio += longitud
        if all(10 <= len(x) <= 1400 for x in grupos):
            return grupos
        # Solo aumenta si hay bloques demasiado largos; aumentar el
        # número de partes no resolvería un bloque demasiado corto.
        if any(len(x) < 10 for x in grupos):
            break
        piezas += 1
    raise ValueError(
        "No se puede dividir el texto en fragmentos TTS de entre "
        "10 y 1400 caracteres sin perder palabras"
    )


def adaptar_escenas(plan):
    formato = plan["formato"]
    if formato not in ("short", "largo"):
        raise ValueError("Formato desconocido")
    # El TTS cobra por petición; en largos se usan bloques de ~50 palabras
    # y mostramos un resumen visual, sin alterar lo que narra la voz.
    limite = 50 if formato == "largo" else 30
    salida = []
    for esc in plan["escenas"]:
        for trozo in fragmentar(esc["texto"], limite):
            if trozo:
                salida.append({"tipo": esc["tipo"], "texto": trozo})
    if not salida or len(salida) > 95:
        raise ValueError("Demasiadas escenas o contenido vacío")
    return salida



def resumen_visual(escena, formato):
    """Acorta solo el rótulo, no el guion hablado ni las fuentes.

    En los largos Gemini lee el texto entero en una petición por bloque.
    No tendría sentido mostrar 50 palabras simultáneamente en una tarjeta.
    """
    palabras = escena["texto"].strip().split()
    limite = 22 if formato == "largo" else 30
    texto = " ".join(palabras[:limite])
    if len(palabras) > limite:
        texto = texto.rstrip(".,;:") + "…"
    return {"tipo": escena["tipo"], "texto": texto}


def imagen_horizontal(escena, i, total, titulo, ruta):
    w,h=RES_WIDE
    img=Image.new("RGB", (w,h), (8,15,29))
    d=ImageDraw.Draw(img)
    for y in range(h):
        a=y/h
        d.line((0,y,w,y), fill=(int(7+9*a),int(13+12*a),int(28+16*a)))
    d.rounded_rectangle((55,48,w-55,116), radius=18, fill=(23,46,64))
    d.text((82,65), "PÍXEL FEROZ", font=fuente(28,True), fill=(58,236,223))
    d.text((76,158), "ANÁLISIS DE VIDEOJUEGOS",font=fuente(25),fill=(255,102,171))
    d.rounded_rectangle((65,228,w-65,585), radius=30,fill=(20,31,52))
    texto=escena["texto"]
    for tam in range(52,27,-2):
        f=fuente(tam,True)
        lineas=partir_lineas(d,texto,f,w-175)
        paso=int(tam*1.35)
        if len(lineas)*paso <= 300:
            break
    if len(lineas)*paso>300:
        raise ValueError("Escena demasiado larga para gráfico")
    y=407-len(lineas)*paso/2
    for linea in lineas:
        d.text((91,int(y)),linea,font=f,fill=(247,250,255))
        y+=paso
    d.text((78,615),titulo[:64],font=fuente(24),fill=(181,208,227))
    d.text((78,663),f"{i+1:02d} / {total:02d}   •   Fuentes en la descripción",
           font=fuente(18),fill=(95,174,186))
    img.save(ruta)


def crear_miniatura(titulo, formato, ruta):
    w,h=(1280,720) if formato=="largo" else (720,1280)
    img=Image.new("RGB",(w,h),(8,14,29))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle((30,30,w-30,h-30),radius=35,outline=(45,232,218),width=8)
    d.text((64,55),"PÍXEL FEROZ",font=fuente(35,True),fill=(59,232,223))
    tam=78 if formato=="largo" else 54
    maximo=w-140
    while tam>=28:
        f=fuente(tam,True)
        lineas=partir_lineas(d,titulo.upper(),f,maximo)
        if len(lineas)*int(tam*1.35) < h*0.55:
            break
        tam-=4
    paso=int(tam*1.35)
    y=h/2-len(lineas)*paso/2
    for linea in lineas:
        d.text((70,int(y)),linea,font=f,fill=(255,252,255))
        y+=paso
    d.text((70,h-100),"VIDEOJUEGOS · NOVEDADES VERIFICADAS",
           font=fuente(22),fill=(255,99,169))
    img.save(ruta,quality=92,optimize=True)



def montar(plan, guion):
    """Crea escenas MP4 sincronizadas individualmente y las concatena.

    Cada escena tiene su propio audio, con un breve silencio final. A diferencia
    del montaje anterior, no aproxima duraciones a partir de número de palabras.
    """
    if plan.get("estado") != "BORRADOR_PENDIENTE_REVISION":
        raise ValueError("Borrador editorial inválido")
    if plan.get("publicacion_automatica") is not False:
        raise ValueError("No se permite publicación automática")
    formato = plan.get("formato")
    if formato not in ("short", "largo"):
        raise ValueError("Formato desconocido")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg y FFprobe son obligatorios")

    escenas = adaptar_escenas(plan)
    reconstruido = " ".join(escena["texto"] for escena in escenas)
    if re.sub(r"\s+", " ", guion).strip() != reconstruido.strip():
        raise ValueError("El guion y el orden de las escenas no coinciden")

    estimar_consumo(escenas, formato)
    narrador = NarradorGemini(formato, plan)
    SALIDA.mkdir(parents=True, exist_ok=True)
    fps = 20
    duracion_total = 0.0
    with tempfile.TemporaryDirectory(prefix="pixel_feroz_render_") as temporal:
        directorio = Path(temporal)
        clip_de_juego = descargar_clip(plan["tema_id"], directorio / "gameplay.mp4")
        clips = []
        for indice, escena in enumerate(escenas):
            audio = directorio / f"audio_{indice:03}.wav"
            duracion_audio = narrador.narrar(escena["texto"], audio)
            # Exactamente un número entero de fotogramas por escena.
            fotogramas = max(1, int(math.ceil((duracion_audio + 0.22) * fps)))
            duracion_escena = fotogramas / fps
            usa_material = (
                clip_de_juego is not None
                and indice % 3 != 2
                and escena["tipo"] != "cierre"
            )
            escena_visible = resumen_visual(escena, formato)
            imagen = directorio / f"escena_{indice:03}.png"
            if usa_material:
                overlay_clips(
                    escena_visible, plan["titulo_propuesto"], formato, imagen
                )
            elif formato == "short":
                tarjeta_escena(
                    escena_visible, indice, len(escenas),
                    plan["titulo_propuesto"], imagen
                )
            else:
                imagen_horizontal(
                    escena_visible, indice, len(escenas),
                    plan["titulo_propuesto"], imagen
                )

            clip = directorio / f"clip_{indice:03}.mp4"
            audio_filtro = (
                "aresample=48000,apad,"
                f"atrim=duration={duracion_escena:.6f},"
                "asetpts=N/SR/TB"
            )
            w, h = RES_SHORT if formato == "short" else RES_WIDE
            if usa_material:
                # El clip se carga SIN su audio: narración propia en español.
                # Solo se reutilizan materiales descargados con derechos
                # confirmados explícitamente para el tema actual.
                comando_video = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-stream_loop", "-1", "-i", str(clip_de_juego),
                    "-loop", "1", "-framerate", str(fps), "-i", str(imagen),
                    "-i", str(audio),
                    "-filter_complex",
                    (
                        f"[0:v]fps={fps},"
                        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                        f"crop={w}:{h},setsar=1,format=yuv420p[base];"
                        "[base][1:v]overlay=0:0:shortest=0[v]"
                    ),
                    "-map", "[v]", "-map", "2:a:0"
                ]
            else:
                # Animación original con movimiento suave: no una imagen
                # completamente inmóvil durante cada escena.
                comando_video = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-loop", "1", "-framerate", str(fps),
                    "-i", str(imagen),
                    "-i", str(audio),
                    "-filter_complex",
                    (
                        f"[0:v]zoompan=z='min(zoom+0.00035,1.055)':"
                        f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                        f"d=1:s={w}x{h}:fps={fps}[v]"
                    ),
                    "-map", "[v]", "-map", "1:a:0"
                ]
            comando(comando_video + [
                "-af", audio_filtro,
                "-frames:v", str(fotogramas),
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "25", "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-c:a", "aac", "-ar", "48000", "-ac", "1",
                "-b:a", "128k",
                "-t", f"{duracion_escena:.6f}",
                str(clip)
            ])
            if clip.stat().st_size < 1000:
                raise RuntimeError(f"El fragmento {indice} no se generó")
            clips.append(clip)
            duracion_total += duracion_escena

        lista = directorio / "clips.txt"
        lista.write_text(
            "".join(f"file '{archivo.name}'\n" for archivo in clips),
            encoding="utf-8"
        )
        salida = SALIDA / (
            "pixel_feroz_short.mp4" if formato == "short"
            else "pixel_feroz_largo.mp4"
        )
        # Los fragmentos comparten FPS, codec, tamaño y formato de audio.
        # No es necesario recodificar el montaje final.
        comando([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(lista),
            "-map", "0:v:0", "-map", "0:a:0", "-c", "copy",
            "-movflags", "+faststart", str(salida)
        ])
        if salida.stat().st_size < 20_000:
            raise RuntimeError("MP4 vacío o incompleto")

        crear_miniatura(plan.get("texto_miniatura", plan["titulo_propuesto"]),
                        formato, SALIDA / "miniatura.jpg")
        print("Archivo:", salida, flush=True)
        print("Clip autorizado incorporado:", bool(clip_de_juego), flush=True)
        print("Motor de voz natural: Gemini 3.8 Flash TTS", flush=True)
        print("Narrador del vídeo:", narrador.voz, flush=True)
        print("Peticiones TTS realizadas:", narrador.peticiones, flush=True)
        print("Escenas:", len(escenas),
              "| Duración planificada:", round(duracion_total, 2),
              "segundos", flush=True)
        print("La publicación requiere autorización y revisión humana.", flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,default=SALIDA/"plan.json")
    p.add_argument("--guion",type=Path,default=SALIDA/"guion.txt")
    args=p.parse_args()
    plan=json.loads(args.plan.read_text(encoding="utf-8"))
    guion=args.guion.read_text(encoding="utf-8").strip()
    montar(plan,guion)


if __name__=="__main__":
    main()
