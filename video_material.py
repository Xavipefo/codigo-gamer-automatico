"""Descarga opcional de clips autorizados, sin extraer material de plataformas.

El secreto PF_CLIPS_JSON contiene un mapa tema_id -> {"url": "HTTPS...",
"derechos_confirmados": true}. Su ausencia usa animaciones originales.
Nunca imprime URLs firmadas. No incluye ni publica los clips en GitHub.
"""
import ipaddress
import json
import os
import socket
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

BLOQUEADOS = {"youtube.com", "youtu.be", "tiktok.com", "instagram.com",
              "rockstargames.com", "vimeo.com"}
LIMITE = 120 * 1024 * 1024


def url_segura(url):
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("URL de vídeo no válida")
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("Solo se admiten enlaces directos HTTPS sin credenciales")
    host = host.lower()
    if host == "localhost" or any(
        host == x or host.endswith("." + x) for x in BLOQUEADOS
    ):
        raise ValueError("No se admiten URLs de vídeos de terceros ni plataformas")
    try:
        direcciones = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("No se puede resolver el servidor de clips") from exc
    for item in direcciones:
        addr = ipaddress.ip_address(item[4][0])
        if not addr.is_global:
            raise ValueError("El servidor de clips no puede usar red privada")
    if not parsed.path.lower().endswith((".mp4", ".mov", ".webm")):
        raise ValueError("Se necesita un enlace directo a MP4, MOV o WebM")
    return url


def descargar_clip(tema_id, destino):
    configuracion = os.environ.get("PF_CLIPS_JSON", "").strip()
    if not configuracion:
        print("Visuales: animación original, sin clip de juego configurado.")
        return None
    try:
        claves = json.loads(configuracion)
    except ValueError as exc:
        raise ValueError("PF_CLIPS_JSON no es un JSON válido") from exc
    if not isinstance(claves, dict):
        raise ValueError("PF_CLIPS_JSON debe ser un objeto JSON")
    item = claves.get(tema_id)
    if item is None:
        print("No hay clip autorizado para este tema; gráficos originales.")
        return None
    if not isinstance(item, dict) or item.get("derechos_confirmados") is not True:
        raise ValueError("El clip requiere confirmación explícita de derechos")
    url_segura(item.get("url"))
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".part")
    try:
        peticion = urllib.request.Request(
            item["url"], headers={"User-Agent": "PixelFerozMedia/1.0"}
        )
        # Evitar imprimir errores con enlaces privados firmados.
        try:
            with urllib.request.urlopen(peticion, timeout=60) as r, temporal.open("wb") as f:
                tipo = r.headers.get("Content-Type", "").lower()
                if "text/html" in tipo or "application/json" in tipo:
                    raise ValueError("El enlace no devuelve material de vídeo")
                while True:
                    fragmento = r.read(1024 * 1024)
                    if not fragmento:
                        break
                    f.write(fragmento)
                    if f.tell() > LIMITE:
                        raise ValueError("Clip superior a 120 MB")
        except OSError as exc:
            raise RuntimeError("No se pudo descargar el clip autorizado") from None
        if temporal.stat().st_size < 20000:
            raise ValueError("Clip descargado vacío")
        temporal.replace(destino)
        resultado = subprocess.run([
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(destino)
        ], capture_output=True, text=True, check=True, timeout=30)
        meta = json.loads(resultado.stdout)
        if not any(s.get("codec_type") == "video" for s in meta.get("streams", [])):
            raise ValueError("El archivo no contiene vídeo")
        segundos = float(meta.get("format", {}).get("duration", 0))
        if not 2 <= segundos <= 600:
            raise ValueError("Clip fuera del intervalo permitido: 2–600 segundos")
        print("Clip de juego autorizado descargado y verificado, segundos:",
              round(segundos, 1), flush=True)
        return destino
    finally:
        temporal.unlink(missing_ok=True)


def overlay_clips(escena, titulo, formato, destino):
    from PIL import Image, ImageDraw
    from generar_short import fuente, partir_lineas

    ancho, alto = (720, 1280) if formato == "short" else (1280, 720)
    lienzo = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(lienzo)
    d.rounded_rectangle(
        (24, 26, ancho - 24, 92),
        radius=16, fill=(5, 14, 30, 215)
    )
    d.text((44, 39), "PÍXEL FEROZ", font=fuente(27, True), fill=(65, 242, 218))
    panel = (26, alto - 475, ancho - 26, alto - 80) if formato == "short" else (
        35, alto - 330, ancho - 35, alto - 40
    )
    d.rounded_rectangle(panel, radius=25, fill=(5, 14, 29, 218))
    d.rounded_rectangle(panel, radius=25, outline=(50, 215, 212, 220), width=2)
    d.text((panel[0] + 24, panel[1] + 18), "NOVEDAD DE VIDEOJUEGOS",
           font=fuente(23, True), fill=(255, 116, 180))
    texto = escena["texto"]
    tam = 35 if formato == "short" else 36
    for sz in range(tam, 23, -2):
        f = fuente(sz, True)
        lineas = partir_lineas(d, texto, f, panel[2] - panel[0] - 60)
        paso = int(sz * 1.35)
        if len(lineas) * paso <= panel[3] - panel[1] - 115:
            break
    else:
        raise ValueError("Escena demasiado larga para el overlay")
    y = panel[1] + 82
    for linea in lineas:
        d.text((panel[0] + 30, y), linea, font=f, fill=(247, 250, 255))
        y += paso
    lienzo.save(destino)
