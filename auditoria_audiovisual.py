#!/usr/bin/env python3
"""QC-01: prueba técnica y muestra visual del MP4 ANTES de subirlo a YouTube.

Conserva la revisión humana: no interpreta el significado de una fotografía.
Solo bloquea errores deterministas: MP4 ausente, sin voz, con imagen negra
o congelada, proporción errónea o desincronización grave.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

W, H = 64, 36
POSICIONES = (0.17, 0.38, 0.61, 0.83)


def ejecutar(argumentos, tiempo=65):
    resultado = subprocess.run(argumentos, capture_output=True, timeout=tiempo)
    if resultado.returncode:
        raise RuntimeError(
            "ffmpeg/ffprobe falló: " +
            resultado.stderr.decode("utf-8", "replace")[-700:]
        )
    return resultado


def obtener_datos(archivo):
    info = json.loads(ejecutar([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(archivo)
    ]).stdout)
    formato = info.get("format", {})
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return formato, v, a


def muestra(archivo, segundos):
    salida = ejecutar([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss",
        f"{segundos:.3f}", "-i", str(archivo), "-an", "-frames:v", "1",
        "-vf", f"scale={W}:{H}", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"
    ], tiempo=30).stdout
    if len(salida) != W * H * 3:
        raise ValueError("No se puede decodificar un fotograma del MP4")
    return salida


def brillo(frame):
    return sum(frame) / (len(frame) * 255.0)


def diferencia(a, b):
    return sum(abs(x-y) for x, y in zip(a, b)) / (len(a)*255.0)


def maximo_audio(archivo, segundos):
    salida = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-ss", f"{segundos:.3f}",
        "-i", str(archivo), "-t", "6", "-vn", "-af", "volumedetect",
        "-f", "null", "-"
    ], capture_output=True, timeout=45)
    if salida.returncode:
        raise RuntimeError("No se ha podido medir la voz del MP4")
    texto = salida.stderr.decode("utf-8", "replace")
    hallado = re.search(r"max_volume:\s*(-?(?:inf|\d+(?:\.\d+)?))\s*dB", texto)
    if not hallado:
        raise ValueError("No hay nivel de audio medible")
    valor = hallado.group(1)
    return float("-inf") if valor == "-inf" else float(valor)


def auditar(archivo, orientacion, minimo=8, maximo=3600):
    archivo = Path(archivo)
    if not archivo.is_file() or archivo.stat().st_size < 10000:
        raise ValueError("Vídeo ausente o vacío")
    fmt, video, audio = obtener_datos(archivo)
    if not video or not audio:
        raise ValueError("MP4 sin pista de vídeo o sin narración")
    dur = float(fmt.get("duration", 0))
    if not minimo <= dur <= maximo:
        raise ValueError(f"Duración fuera del rango admitido: {dur:.1f}s")
    ancho, alto = int(video.get("width", 0)), int(video.get("height", 0))
    ratio = ancho/max(1, alto)
    if ancho < 300 or alto < 160:
        raise ValueError("Resolución insuficiente")
    if orientacion == "vertical" and not .48 <= ratio <= .72:
        raise ValueError("Formato vertical incorrecto")
    if orientacion == "horizontal" and not 1.55 <= ratio <= 1.95:
        raise ValueError("Formato horizontal incorrecto")

    for pista in (video, audio):
        if pista.get("duration") and abs(float(pista["duration"])-dur)>max(4.5,.05*dur):
            raise ValueError("Desajuste grave de duraciones de audio/vídeo")

    instantaneas=[muestra(archivo,max(.2,dur*p)) for p in POSICIONES]
    luminosidad=[round(brillo(f),4) for f in instantaneas]
    if sum(b<.018 for b in luminosidad)>=3:
        raise ValueError("Vídeo casi negro en la mayoría de muestras")
    cambios=[round(diferencia(instantaneas[i],instantaneas[i+1]),4)
             for i in range(len(instantaneas)-1)]
    if max(cambios, default=0)<.005:
        raise ValueError("Vídeo visualmente congelado en toda la duración")

    audios=[maximo_audio(archivo,max(0,dur*p-3)) for p in (.18,.51,.81)]
    if max(audios)<-52:
        raise ValueError("Narración ausente o prácticamente inaudible")
    return {
        "version":"QC-01","archivo":archivo.name,
        "orientacion":orientacion,"duracion_segundos":round(dur,2),
        "resolucion":[ancho,alto],
        "brillos_muestras":luminosidad,
        "cambios_entre_muestras":cambios,
        "audio_max_db":[v if v!=float("-inf") else None for v in audios],
        "estado":"apto_tecnicamente_para_revision_privada",
        "pendiente_revision_editorial":True,
        "alcance":"No comprueba si fotografías y narración tratan del mismo tema.",
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video",required=True)
    p.add_argument("--orientacion",choices=("vertical","horizontal"),required=True)
    p.add_argument("--minimo",type=float,default=8)
    p.add_argument("--maximo",type=float,default=3600)
    p.add_argument("--informe",required=True)
    args=p.parse_args()
    try:
        resultado=auditar(args.video,args.orientacion,args.minimo,args.maximo)
    except Exception as e:
        reporte={"version":"QC-01","estado":"rechazado","razon":str(e),
                 "pendiente_revision_editorial":True}
        ruta=Path(args.informe);ruta.parent.mkdir(parents=True,exist_ok=True)
        ruta.write_text(json.dumps(reporte,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise
    ruta=Path(args.informe);ruta.parent.mkdir(parents=True,exist_ok=True)
    ruta.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(resultado,ensure_ascii=False))


if __name__=="__main__":
    main()
