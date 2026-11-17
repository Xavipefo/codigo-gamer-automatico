"""Clips autorizados para Shorts/largos, sin descargar de plataformas.

PF_CLIPS_JSON (Secret):
{
 "gta6-tema":[
  {"url":"https://cdn-propia.example/clip1.mp4",
   "derechos_confirmados":true,"origen":"propio",
   "credito":"Píxel Feroz",
   "fuente_publica":"https://sitio-propio.example/creditos"},
  {"url":"https://cdn-propia.example/clip2.mp4",
   "derechos_confirmados":true,"origen":"licenciado",
   "credito":"Autor", "fuente_publica":"https://autor.example/licencia"}
 ]
}
Se sigue admitiendo la entrada antigua de un único objeto por tema.
Los clips se descargan solo de archivos directos con derechos comprobados;
no se extraen de Rockstar, YouTube ni otras páginas de reproducción.
"""
import ipaddress
import json
import math
import os
import socket
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

BLOQUEADOS = {
    "youtube.com", "youtu.be", "tiktok.com", "instagram.com",
    "rockstargames.com", "vimeo.com", "dailymotion.com",
}
ORIGENES = {"propio", "ia_original", "licenciado", "oficial_autorizado"}
LIMITE = 120 * 1024 * 1024
MAX_CLIPS = 6


def url_segura(url):
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("URL de vídeo no válida")
    try:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname
        puerto = parsed.port
    except ValueError:
        raise ValueError("URL de vídeo mal formada") from None
    if parsed.scheme != "https" or not host or puerto not in (None, 443):
        raise ValueError("Solo se admiten enlaces directos HTTPS puerto 443")
    if parsed.username or parsed.password:
        raise ValueError("URL de vídeo con credenciales")
    host = host.lower().strip(".")
    if host == "localhost" or any(
        host == x or host.endswith("." + x) for x in BLOQUEADOS
    ):
        raise ValueError("No se admiten URLs de plataformas de vídeo")
    if not parsed.path.lower().endswith((".mp4", ".mov", ".webm")):
        raise ValueError("Se necesita enlace directo a MP4, MOV o WebM")
    try:
        direcciones = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        raise ValueError("No se puede resolver el servidor de clips") from None
    if not direcciones or any(
        not ipaddress.ip_address(item[4][0]).is_global
        for item in direcciones
    ):
        raise ValueError("El servidor de clips no puede usar red privada")
    return url


def catalogo_clips(tema_id):
    raw = os.environ.get("PF_CLIPS_JSON", "").strip()
    if not raw:
        return []
    try:
        manifiesto = json.loads(raw)
    except (ValueError, TypeError):
        raise ValueError("PF_CLIPS_JSON no contiene JSON válido") from None
    if not isinstance(manifiesto, dict):
        raise ValueError("PF_CLIPS_JSON debe ser un objeto por temas")
    grupo = manifiesto.get(tema_id)
    if grupo is None:
        return []
    lista = [grupo] if isinstance(grupo, dict) else grupo
    if not isinstance(lista, list) or not 1 <= len(lista) <= MAX_CLIPS:
        raise ValueError("Se admiten de 1 a 6 clips por tema")
    for item in lista:
        if not isinstance(item, dict) or item.get("derechos_confirmados") is not True:
            raise ValueError("Cada clip requiere derechos confirmados")
        # El manifiesto antiguo de un solo clip requería exclusivamente
        # URL y derechos_confirmados. Si se usa ese formato no inventamos
        # un crédito: lo marcamos como pendiente de atribución explícita.
        antiguo = isinstance(grupo, dict) and not any(
            k in item for k in ("origen", "credito", "fuente_publica")
        )
        if not antiguo:
            if item.get("origen") not in ORIGENES:
                raise ValueError("Origen de clip desconocido o no autorizado")
            if not isinstance(item.get("credito"), str) or not 2 <= len(item["credito"]) <= 90:
                raise ValueError("Falta crédito de clip")
            u = urllib.parse.urlsplit(item.get("fuente_publica", ""))
            if u.scheme != "https" or not u.hostname:
                raise ValueError("Falta página pública para atribución del clip")
        url_segura(item.get("url"))
    return lista


def creditos_clips(tema_id):
    return list(dict.fromkeys(
        f"{x['credito']} — {x['fuente_publica']}"
        for x in catalogo_clips(tema_id)
        if x.get("credito") and x.get("fuente_publica")
    ))


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise ValueError("No se siguen redirecciones para clips")


def _download_verificado(item, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".part")
    try:
        req = urllib.request.Request(
            item["url"], headers={"User-Agent": "PixelFerozMedia/2.0"}
        )
        opener = urllib.request.build_opener(_SinRedirecciones())
        try:
            with opener.open(req, timeout=60) as resp, temporal.open("wb") as archivo:
                tipo = resp.headers.get("Content-Type", "").lower()
                if any(x in tipo for x in ("text/", "html", "json", "xml")):
                    raise ValueError("El enlace no devuelve material de vídeo")
                while True:
                    bloque = resp.read(1024 * 1024)
                    if not bloque:
                        break
                    archivo.write(bloque)
                    if archivo.tell() > LIMITE:
                        raise ValueError("Clip superior a 120 MB")
        except (OSError, urllib.error.URLError):
            raise RuntimeError("No se pudo descargar un clip autorizado") from None
        if temporal.stat().st_size < 20000:
            raise ValueError("Clip descargado vacío")
        informacion = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format",
             "-of", "json", str(temporal)],
            capture_output=True, text=True, check=True, timeout=30
        )
        meta = json.loads(informacion.stdout)
        if not any(x.get("codec_type") == "video" for x in meta.get("streams", [])):
            raise ValueError("Archivo sin pista de vídeo")
        duracion = float(meta.get("format", {}).get("duration", 0))
        if not math.isfinite(duracion) or not 2 <= duracion <= 180:
            raise ValueError("Clip no apto: duración fuera de 2–180 s")
        temporal.replace(destino)
        return duracion
    finally:
        temporal.unlink(missing_ok=True)


def descargar_clips(tema_id, directorio):
    elementos = catalogo_clips(tema_id)
    if not elementos:
        print("No hay clips con derechos confirmados para este tema; se usarán otros visuales.")
        return []
    directorio = Path(directorio)
    resultado = []
    for indice, item in enumerate(elementos):
        # Respeta extensión real para que FFmpeg pueda reconocer el archivo.
        extension = Path(urllib.parse.urlsplit(item["url"]).path).suffix.lower()
        ruta = directorio / f"clip_autorizado_{indice:02d}{extension}"
        duracion = _download_verificado(item, ruta)
        resultado.append({
            "ruta": ruta, "segundos": duracion,
            "credito": item.get("credito", "Material autorizado del canal"),
            "origen": item.get("origen", "licencia_previa"),
        })
    print("Clips con derechos confirmados:", len(resultado), flush=True)
    return resultado


def descargar_clip(tema_id, destino):
    """Adaptador del manifest anterior: devuelve un solo archivo o None."""
    destino = Path(destino)
    archivos = descargar_clips(tema_id, destino.parent)
    if not archivos:
        return None
    principal = archivos[0]["ruta"]
    principal.replace(destino)
    return destino


def overlay_clips(escena, titulo, formato, destino, credito=""):
    """Overlay breve: el vídeo ocupa casi toda la pantalla."""
    from PIL import Image, ImageDraw
    from generar_short import fuente, partir_lineas

    w, h = (720, 1280) if formato == "short" else (1280, 720)
    imagen = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(imagen)
    banda_alta = 70 if formato == "largo" else 83
    d.rounded_rectangle((26, 24, w-26, banda_alta),
                        radius=12, fill=(5, 14, 30, 200))
    d.text((44, 37), "PÍXEL FEROZ", font=fuente(24, True),
           fill=(65, 242, 218))
    y0 = int(h * (.79 if formato == "largo" else .81))
    d.rounded_rectangle((25, y0, w-25, h-40),
                        radius=18, fill=(4, 12, 24, 196))
    texto = escena["texto"]
    for tam in range(36 if formato == "largo" else 33, 20, -2):
        f = fuente(tam, True)
        lineas = partir_lineas(d, texto, f, w-100)
        if len(lineas) <= 2:
            break
    for indice, linea in enumerate(lineas[:2]):
        d.text((49, y0 + 18 + indice * int(tam * 1.2)),
               linea, font=f, fill=(248, 250, 255))
    if credito:
        d.text((30, h-27), "Vídeo: " + credito[:58],
               font=fuente(14), fill=(230, 230, 230))
    imagen.save(destino)
