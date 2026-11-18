"""Subplanos de 4–8 s para reportajes con material visual oficial de GTA VI.

Usa FFmpeg directamente. Cada segmento narrado conserva su audio íntegro
y cambia entre capturas y clips breves; nunca utiliza música del juego.
"""
import math
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
from generar_short import fuente, partir_lineas

W,H,FPS=1280,720,20

def repartir_frames(frames,max_por_plano=FPS*7):
    if frames<1:
        raise ValueError("La escena no tiene fotogramas")
    cantidad=math.ceil(frames/max_por_plano)
    base,resto=divmod(frames,cantidad)
    return [base+(1 if i<resto else 0) for i in range(cantidad)]

def rotulo_editorial(escena,destino):
    capa=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(capa)
    d.rounded_rectangle((26,22,W-26,88),radius=15,fill=(4,14,29,208))
    d.text((47,41),"PÍXEL FEROZ  |  GTA VI",font=fuente(24,True),fill=(64,238,221))
    d.rounded_rectangle((24,575,W-24,693),radius=18,fill=(3,13,28,209))
    palabras=escena["texto"].strip().split()
    frase=" ".join(palabras[:10])
    if len(palabras)>10:
        frase=frase.rstrip(".,;:")+"…"
    dtexto=ImageDraw.Draw(capa)
    for tam in range(31,21,-2):
        f=fuente(tam,True)
        lineas=partir_lineas(dtexto,frase,f,W-92)
        if len(lineas)<=2:
            break
    for i,linea in enumerate(lineas[:2]):
        dtexto.text((46,592+i*38),linea,font=f,fill=(249,252,255))
    dtexto.text((29,697),"Material oficial de Rockstar Games · análisis editorial",
                font=fuente(13),fill=(220,230,234))
    destino=Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    capa.save(destino)
    return destino

def elegir_tomas(fotos,clips,fotogramas,indice):
    """Plano real distinto cada ~7 segundos; hasta un clip cada 5 tomas."""
    if not fotos:
        raise ValueError("Se necesita al menos una foto oficial")
    cuenta=repartir_frames(fotogramas)
    tomas=[]
    for i,frames in enumerate(cuenta):
        foto,credito,titulo=fotos[(indice*3+i)%len(fotos)]
        if clips and (i+indice*3)%5==0 and len(cuenta)>1:
            fuente_clip=clips[(i+indice)%len(clips)]
            tomas.append({"tipo":"clip","ruta":Path(fuente_clip["ruta"]),
                          "frames":frames,"credito":fuente_clip["credito"],
                          "titulo":fuente_clip.get("nombre","Clip oficial")})
        else:
            tomas.append({"tipo":"foto","ruta":Path(foto),
                          "frames":frames,"credito":credito,"titulo":titulo})
    return tomas

def crear_preview(toma,capa,destino):
    destino=Path(destino)
    destino.parent.mkdir(parents=True,exist_ok=True)
    if toma["tipo"]=="clip":
        temporal=destino.with_suffix(".fotograma.png")
        try:
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-y",
                "-ss","0.3","-i",str(toma["ruta"]),"-frames:v","1",str(temporal)
            ],check=True,timeout=30)
            with Image.open(temporal) as src:
                imagen=ImageOps.fit(src.convert("RGB"),(W,H))
        finally:
            temporal.unlink(missing_ok=True)
    else:
        with Image.open(toma["ruta"]) as src:
            imagen=ImageOps.fit(src.convert("RGB"),(W,H))
    with Image.open(capa) as im:
        imagen=Image.alpha_composite(imagen.convert("RGBA"),im.convert("RGBA")).convert("RGB")
    imagen.save(destino,quality=83,optimize=True)
    return destino

def renderizar(tomas,capa,audio,destino,comando):
    """Un solo MP4 por bloque de voz; concatena subplanos sin alterar la voz."""
    if not tomas:
        raise ValueError("Ninguna toma para render")
    entrada=["ffmpeg","-hide_banner","-loglevel","error","-y"]
    filtros=[]
    for i,toma in enumerate(tomas):
        if toma["tipo"]=="clip":
            entrada+=["-stream_loop","-1","-i",str(toma["ruta"])]
            fuente=(f"[{i}:v]fps={FPS},"
                    f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},setsar=1,")
        else:
            entrada+=["-loop","1","-framerate",str(FPS),"-i",str(toma["ruta"])]
            fuente=(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},setsar=1,"
                    f"zoompan=z='min(zoom+0.00030,1.045)':"
                    f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                    f"d=1:s={W}x{H}:fps={FPS},")
        filtros.append(fuente+
                       f"trim=end_frame={toma['frames']},"
                       f"setpts=PTS-STARTPTS[p{i}]")
    entrada+=["-loop","1","-framerate",str(FPS),"-i",str(capa)]
    audio_idx=len(tomas)+1
    entrada+=["-i",str(audio)]
    concatenados="".join(f"[p{i}]" for i in range(len(tomas)))
    filtros.append(f"{concatenados}concat=n={len(tomas)}:v=1:a=0[base]")
    filtros.append(f"[base][{len(tomas)}:v]overlay=0:0:shortest=1,format=yuv420p[v]")
    total=sum(t["frames"] for t in tomas)
    duracion=total/FPS
    filtro_audio=(f"aresample=48000,apad,atrim=duration={duracion:.6f},"
                  "asetpts=N/SR/TB")
    comando(entrada+[
        "-filter_complex",";".join(filtros),"-map","[v]",
        "-map",f"{audio_idx}:a:0","-af",filtro_audio,
        "-frames:v",str(total),
        "-c:v","libx264","-preset","veryfast","-crf","25",
        "-pix_fmt","yuv420p","-r",str(FPS),
        "-c:a","aac","-ar","48000","-ac","1","-b:a","128k",
        "-t",f"{duracion:.6f}",str(destino)
    ])
    if not Path(destino).is_file() or Path(destino).stat().st_size<5000:
        raise RuntimeError("Montaje con subplanos vacío")
    return duracion
