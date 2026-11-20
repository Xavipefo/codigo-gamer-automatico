#!/usr/bin/env python3
"""PF-41: montaje de Shorts GTA VI con subplanos visuales de 2-4 s.

Reutiliza la voz UNA VEZ por bloque, solo fotos ya verificadas del banco
Rockstar y FFmpeg en un único proceso por bloque. No descarga ni publica.
"""
import math
import os
import re
import subprocess
import wave
from array import array
from pathlib import Path

from visuales_autorizados import escena_con_foto

FPS = 20
ANCHO, ALTO = 720, 1280
FOTOS_POR_BLOQUE = 6
MAX_PLANO_FRAMES = 76  # 3,8 s a 20 fps


def repartir_fotogramas(total, maximo=MAX_PLANO_FRAMES):
    if not isinstance(total, int) or total < 1 or maximo < 1:
        raise ValueError("Fotogramas o límite inválidos")
    cantidad = math.ceil(total / maximo)
    base, resto = divmod(total, cantidad)
    trozos = [base + (1 if i < resto else 0) for i in range(cantidad)]
    if sum(trozos) != total or not all(0 < n <= maximo for n in trozos):
        raise RuntimeError("Error al repartir los fotogramas")
    return trozos


def _fragmentos_texto(texto, cantidad):
    """División equilibrada de palabras sin inventar ni alterar el guion."""
    palabras = str(texto).split()
    if not palabras:
        raise ValueError("Bloque de texto vacío")
    base, resto = divmod(len(palabras), cantidad)
    resultado = []
    posicion = 0
    for i in range(cantidad):
        longitud = base + (1 if i < resto else 0)
        trozo = " ".join(palabras[posicion:posicion + longitud])
        posicion += longitud
        resultado.append(trozo)
    return resultado


def contextos_visuales(escenas):
    """Seis consultas por bloque; enfatiza fragmentos según orden narrativo.

    El contexto completo se conserva para no buscar imágenes desconectadas.
    """
    resultado = []
    for escena in escenas:
        texto = escena["texto"]
        trozos = _fragmentos_texto(texto, FOTOS_POR_BLOQUE)
        for trozo in trozos:
            resultado.append({
                "tipo": escena["tipo"],
                "texto": (trozo + " " + texto).strip(),
            })
    return resultado


def preparar_tomas(fotos, escena, fotogramas, carpeta, indice):
    """Prepara los PNG compuestos que mostrarán los diferentes planos.

    Las fotos ya fueron verificadas por rockstar_media.elegir_imagenes.
    """
    reparto = repartir_fotogramas(fotogramas)
    if not fotos:
        raise ValueError("No hay fotos oficiales para las tomas")
    if len(reparto) > len(fotos):
        raise RuntimeError(
            "Bloque demasiado largo para el banco reservado: "
            "reducir el guion o aumentar FOTOS_POR_BLOQUE"
        )
    rotulos = _fragmentos_texto(escena["texto"], len(reparto))
    resultado = []
    carpeta = Path(carpeta)
    for j, (frames, linea) in enumerate(zip(reparto, rotulos)):
        # Repartir las fotos sobre TODA la narración (inicio, centro y
        # final), no solo coger las primeras de las seis consultas.
        posicion = min(
            len(fotos) - 1,
            int((j + 0.5) * len(fotos) / len(reparto))
        )
        foto, credito, titulo = fotos[posicion]
        foto = Path(foto)
        if not foto.is_file():
            raise FileNotFoundError("No existe foto oficial: " + str(foto))
        ruta = carpeta / f"pantalla_{indice:03}_{j:02}.png"
        escena_con_foto(
            {"tipo": escena["tipo"], "texto": linea},
            "short", foto, credito, ruta
        )
        resultado.append({
            "tipo": "foto",
            "archivo": ruta,
            "foto": foto,
            "credito": credito,
            "titulo": titulo,
            "fotogramas": frames,
            "texto": linea,
        })
    return resultado


def _movimiento(i):
    """Tres movimientos suaves y alternos: zoom, paneo derecha, izquierda."""
    if i % 3 == 0:
        return (
            "z='min(zoom+0.00050,1.055)':"
            "x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2'"
        )
    if i % 3 == 1:
        return (
            "z='1.050':x='(iw-iw/zoom)*min(1,on/80)':"
            "y='(ih-ih/zoom)/2'"
        )
    return (
        "z='1.050':x='(iw-iw/zoom)*(1-min(1,on/80))':"
        "y='(ih-ih/zoom)/2'"
    )


def comando_ffmpeg_short(tomas, audio, destino):
    """Construye comando de render en un único proceso FFmpeg por bloque."""
    if not tomas or len(tomas) > FOTOS_POR_BLOQUE:
        raise ValueError("Número de subplanos fuera del límite")
    entrada = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y"
    ]
    filtros = []
    total = 0
    for i, toma in enumerate(tomas):
        frames = toma["fotogramas"]
        if not isinstance(frames, int) or frames <= 0 or frames > MAX_PLANO_FRAMES:
            raise ValueError("Subplano supera 3,8 segundos")
        total += frames
        entrada += [
            "-loop", "1", "-framerate", str(FPS), "-i",
            str(toma["archivo"])
        ]
        filtros.append(
            f"[{i}:v]scale={ANCHO}:{ALTO},"
            f"zoompan={_movimiento(i)}:d=1:"
            f"s={ANCHO}x{ALTO}:fps={FPS},"
            f"trim=end_frame={frames},setpts=PTS-STARTPTS[p{i}]"
        )
    entrada += ["-i", str(audio)]
    filtros.append(
        "".join(f"[p{i}]" for i in range(len(tomas)))
        + f"concat=n={len(tomas)}:v=1:a=0,format=yuv420p[v]"
    )
    duracion = total / FPS
    filtro_audio = (
        f"aresample=48000,apad,atrim=duration={duracion:.6f},"
        "asetpts=N/SR/TB"
    )
    return entrada + [
        "-filter_complex", ";".join(filtros),
        "-map", "[v]", "-map", f"{len(tomas)}:a:0",
        "-af", filtro_audio,
        "-frames:v", str(total),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-ar", "48000", "-ac", "1", "-b:a", "128k",
        "-t", f"{duracion:.6f}", str(destino)
    ]


def renderizar_short(tomas, audio, destino, comando):
    orden = comando_ffmpeg_short(tomas, audio, destino)
    comando(orden)
    destino = Path(destino)
    if not destino.is_file() or destino.stat().st_size < 5000:
        raise RuntimeError("El MP4 de subplanos está vacío")
    return sum(x["fotogramas"] for x in tomas) / FPS


def compactar_pausas_wav(ruta, minimo=0.75, conservar=0.28):
    """Quita el EXCESO de silencio TTS sin cortar fonemas ni cambiar tono.

    - Solo WAV PCM16 mono con señal hablada.
    - Umbral conservador -46 dBFS (~160 de 32768).
    - Nunca toca pausas cortas (<750 ms) ni vídeos largos.
    - Si no hay voz suficiente, deja intacto el audio para evitar sorpresas.
    """
    ruta = Path(ruta)
    with wave.open(str(ruta), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            return wf.getnframes() / wf.getframerate()
        frecuencia = wf.getframerate()
        datos = wf.readframes(wf.getnframes())
    muestras = array("h")
    muestras.frombytes(datos)
    if not muestras or frecuencia <= 0:
        raise ValueError("Audio TTS vacío")
    tam = max(1, int(frecuencia * 0.02))
    rms = []
    for pos in range(0, len(muestras), tam):
        bloque = muestras[pos:pos + tam]
        rms.append(math.sqrt(sum(x * x for x in bloque) / len(bloque)))
    if max(rms) < 350:
        return len(muestras) / frecuencia
    limite = min(180, max(110, max(rms) * 0.012))
    es_silencio = [v <= limite for v in rms]
    intervalos = []
    inicio = None
    for i, silencio in enumerate(es_silencio + [False]):
        if silencio and inicio is None:
            inicio = i
        elif not silencio and inicio is not None:
            fin = i
            if (fin - inicio) * tam / frecuencia >= minimo:
                a, b = inicio * tam, min(len(muestras), fin * tam)
                intervalos.append((a, b))
            inicio = None
    if not intervalos:
        return len(muestras) / frecuencia
    # Mantener 140 ms anteriores y 140 ms posteriores en pausas largas.
    conservadas = []
    pos = 0
    for a, b in intervalos:
        exceso = max(0, b-a-int(conservar * frecuencia))
        if exceso == 0:
            continue
        primera_parte = int((b-a-exceso) / 2)
        izquierda, derecha = a + primera_parte, b - (b-a-exceso-primera_parte)
        conservadas.append(muestras[pos:izquierda])
        pos = derecha
    conservadas.append(muestras[pos:])
    reducido = array("h")
    for parte in conservadas:
        reducido.extend(parte)
    original = len(muestras) / frecuencia
    final = len(reducido) / frecuencia
    if not (0.45 * original <= final <= original) or final < 0.6:
        return original
    temporal = ruta.with_suffix(".compacto.tmp.wav")
    try:
        with wave.open(str(temporal), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(frecuencia)
            wf.writeframes(reducido.tobytes())
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)
    if original - final >= 0.15:
        print(
            "PF-41: pausas reducidas",
            round(original-final, 2), "s en el bloque", flush=True
        )
    return final
