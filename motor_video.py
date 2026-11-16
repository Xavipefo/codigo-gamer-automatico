#!/usr/bin/env python3
"""Motor de vídeo: voz por escena, escenas originales y montaje en FFmpeg.

Usa tarjetas gráficas propias; no extrae gameplay ni material audiovisual ajeno.
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from generar_short import tarjeta_escena, fuente, partir_lineas, descargar, URL_MODELO

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
VOZ = BASE / "voz"
RES_WIDE = (1280, 720)
RES_SHORT = (720, 1280)


def comando(args, **kwargs):
    subprocess.run(args, check=True, timeout=900, **kwargs)


def fragmentar(texto, max_palabras):
    palabras = texto.split()
    return [" ".join(palabras[i:i + max_palabras])
            for i in range(0, len(palabras), max_palabras)]


def adaptar_escenas(plan):
    formato = plan["formato"]
    if formato not in ("short", "largo"):
        raise ValueError("Formato desconocido")
    limite = 27 if formato == "largo" else 30
    salida = []
    for esc in plan["escenas"]:
        for trozo in fragmentar(esc["texto"], limite):
            if trozo:
                salida.append({"tipo": esc["tipo"], "texto": trozo})
    if not salida or len(salida) > 95:
        raise ValueError("Demasiadas escenas o contenido vacío")
    return salida


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


def modelo_piper():
    if not shutil.which("piper"):
        raise RuntimeError("Falta piper-tts. Instala requirements.txt")
    modelo=VOZ/"es_ES-sharvard-medium.onnx"
    descargar(modelo,URL_MODELO)
    descargar(VOZ/"es_ES-sharvard-medium.onnx.json",URL_MODELO+".json")
    return modelo


def narrar(modelo,texto,ruta):
    comando(["piper","--model",str(modelo),"--output_file",str(ruta)],
            input=texto,text=True)
    with wave.open(str(ruta),"rb") as f:
        segundos=f.getnframes()/f.getframerate()
    if segundos < .2:
        raise RuntimeError("El modelo no produjo audio válido")
    return segundos


def montar(plan, guion):
    if plan.get("estado") != "BORRADOR_PENDIENTE_REVISION":
        raise ValueError("Borrador inválido")
    if plan.get("publicacion_automatica") is not False:
        raise ValueError("Este generador no permite publicar automáticamente")
    formato=plan["formato"]
    escenas=adaptar_escenas(plan)
    reconstruido=" ".join(e["texto"] for e in escenas)
    if re.sub(r"\s+"," ",guion).strip() != reconstruido.strip():
        raise ValueError("El texto de la voz debe coincidir exactamente con las escenas")
    modelo=modelo_piper()
    SALIDA.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cg_render_") as tmp:
        td=Path(tmp)
        tiempos=[]
        imagenes=[]
        audios=[]
        for i,escena in enumerate(escenas):
            wav=td/f"{i:03}.wav"
            dur=narrar(modelo,escena["texto"],wav)
            dur+=0.10
            foto=td/f"{i:03}.png"
            if formato=="short":
                tarjeta_escena(escena,i,len(escenas),plan["titulo_propuesto"],foto)
            else:
                imagen_horizontal(escena,i,len(escenas),plan["titulo_propuesto"],foto)
            tiempos.append(dur)
            imagenes.append(foto)
            audios.append(wav)
        lista_fotos=td/"imagenes.txt"
        # concat demuxer concatena fotogramas con duraciones.
        lista_fotos.write_text("".join(
            f"file '{p.name}'\nduration {d:.6f}\n"
            for p,d in zip(imagenes,tiempos)
        )+f"file '{imagenes[-1].name}'\n",encoding="utf-8")
        lista_audio=td/"audios.txt"
        lista_audio.write_text("".join(f"file '{p.name}'\n" for p in audios),
                               encoding="utf-8")
        audio=td/"narracion.m4a"
        comando(["ffmpeg","-hide_banner","-loglevel","error","-y",
                 "-f","concat","-safe","0","-i",str(lista_audio),
                 "-c:a","aac","-b:a","128k",str(audio)])
        video=SALIDA/("pixel_feroz_short.mp4" if formato=="short" else "pixel_feroz_largo.mp4")
        comando(["ffmpeg","-hide_banner","-loglevel","error","-y",
                 "-f","concat","-safe","0","-i",str(lista_fotos),
                 "-i",str(audio),"-vf","fps=20","-c:v","libx264",
                 "-preset","veryfast","-crf","24","-pix_fmt","yuv420p",
                 "-c:a","copy","-shortest","-movflags","+faststart",
                 str(video)])
        if video.stat().st_size < 20000:
            raise RuntimeError("Vídeo incompleto")
        crear_miniatura(plan["titulo_propuesto"],formato,SALIDA/"miniatura.jpg")
        print("MP4 generado:",str(video),"bytes",video.stat().st_size)
        print("Escenas:",len(escenas),"duración narrada:",round(sum(tiempos),1))
        print("Sin publicación. Revisar audio, factualidad, imagen y miniatura.")


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
