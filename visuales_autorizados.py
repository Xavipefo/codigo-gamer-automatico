"""Fotografías autorizadas (propias, IA propia o licencia), con atribución.

PF_IMAGENES_JSON es GitHub Secret opcional. Formato:
{"id-tema":[{"url":"https://cdn.example.com/foto.jpg",
 "derechos_confirmados":true, "origen":"propio|ia_original|licenciado|oficial_autorizado",
 "credito":"Nombre del titular", "fuente_publica":"https://example.com/credito"}]}

Nunca descargar automáticamente de Rockstar, YouTube o fuentes no
autorizadas. Atribuir NO concede por sí mismo derechos.
"""
import ipaddress
import json
import os
import socket
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

TIPOS = {"propio", "ia_original", "licenciado", "oficial_autorizado"}
LIMITE_IMAGEN = 8 * 1024 * 1024


def catalogo(tema_id):
    raw = os.environ.get("PF_IMAGENES_JSON", "").strip()
    if not raw:
        return []
    try:
        datos = json.loads(raw)
    except (ValueError, TypeError):
        raise ValueError("PF_IMAGENES_JSON no contiene JSON válido") from None
    if not isinstance(datos, dict):
        raise ValueError("PF_IMAGENES_JSON debe ser un objeto")
    elementos = datos.get(tema_id, [])
    if not isinstance(elementos, list) or len(elementos) > 10:
        raise ValueError("Máximo 10 imágenes por tema")
    for i,item in enumerate(elementos):
        if not isinstance(item, dict):
            raise ValueError("Cada imagen necesita ficha de licencia")
        if item.get("derechos_confirmados") is not True or item.get("origen") not in TIPOS:
            raise ValueError("Imagen sin derechos confirmados o origen válido")
        if not isinstance(item.get("credito"), str) or not 2 <= len(item["credito"]) <= 80:
            raise ValueError("Imagen sin crédito de titular")
        origen = urllib.parse.urlsplit(item.get("fuente_publica", ""))
        if origen.scheme != "https" or not origen.hostname:
            raise ValueError("Imagen sin fuente pública HTTPS para atribución")
        _validar_url_descarga(item.get("url"))
    return elementos


def _validar_url_descarga(url):
    if not isinstance(url, str) or len(url) > 2000:
        raise ValueError("URL de imagen inválida")
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or not u.hostname or u.port not in (None,443):
        raise ValueError("La imagen debe usar HTTPS")
    if u.username or u.password or not u.path.lower().endswith((".jpg",".jpeg",".png",".webp")):
        raise ValueError("Solo imágenes directas JPG, PNG o WebP")
    host = u.hostname.lower()
    if host in ("localhost", "youtube.com", "rockstargames.com") or any(
        host.endswith("."+p) for p in ("localhost", "youtube.com", "rockstargames.com")
    ):
        raise ValueError("Se necesita un archivo propio o con licencia, no extracción de plataformas")
    try:
        direcciones = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        raise ValueError("Servidor de imagen no resoluble") from None
    if not direcciones or any(
        not ipaddress.ip_address(x[4][0]).is_global for x in direcciones
    ):
        raise ValueError("No se permiten IP privadas/reservadas")


class SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise ValueError("No se siguen redirecciones de imágenes")


def descargar_imagenes(tema_id, directorio):
    lista = catalogo(tema_id)
    if not lista:
        return []
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    recursos = []
    opener = urllib.request.build_opener(SinRedirecciones())
    for i, item in enumerate(lista):
        destino = directorio / f"autorizada_{i}.png"
        try:
            req = urllib.request.Request(
                item["url"], headers={"User-Agent":"PixelFerozRightsChecked/1.0"}
            )
            with opener.open(req, timeout=30) as r:
                tipo = r.headers.get("Content-Type","").lower()
                if not tipo.startswith("image/"):
                    raise ValueError("El recurso no es una imagen")
                data = r.read(LIMITE_IMAGEN + 1)
            if len(data) > LIMITE_IMAGEN or len(data) < 150:
                raise ValueError("Imagen vacía o demasiado grande")
            temporal = destino.with_suffix(".part")
            temporal.write_bytes(data)
            try:
                with Image.open(temporal) as im:
                    im.verify()
                with Image.open(temporal) as im:
                    if im.width * im.height > 18_000_000 or min(im.size) < 400:
                        raise ValueError("Imagen demasiado grande o de baja resolución")
                    limpio = ImageOps.exif_transpose(im).convert("RGB")
                    limpio.thumbnail((2400,1600))
                    limpio.save(destino, format="PNG")
            finally:
                temporal.unlink(missing_ok=True)
            recursos.append((destino, item["credito"]))
        except (OSError, urllib.error.URLError, ValueError):
            # Fallar cerrado: si hay configuración de imagen, no usar de
            # modo silencioso una foto inválida o sin licencia.
            raise RuntimeError("No se pudo validar una imagen declarada autorizada") from None
    print("Visuales autorizados verificados:", len(recursos), flush=True)
    return recursos


def creditos_para_descripcion(tema_id):
    return list(dict.fromkeys(
        f"{x['credito']} — {x['fuente_publica']}" for x in catalogo(tema_id)
    ))


def escena_con_foto(escena, formato, foto, credito, destino):
    """Foto casi a pantalla completa con rótulo muy breve (no muro de texto).

    El zoom/paneo se aplica después por FFmpeg, sobre la escena entera.
    Nunca reutiliza material descargado de redes sin autorización.
    """
    from generar_short import fuente, partir_lineas

    w, h = (720, 1280) if formato == "short" else (1280, 720)
    with Image.open(foto) as original:
        fondo = ImageOps.fit(
            original.convert("RGB"), (w, h), method=Image.Resampling.LANCZOS
        )
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.rounded_rectangle(
        (24, 20, w - 24, 84), radius=14, fill=(4, 12, 25, 183)
    )
    d.text((48, 37), "PÍXEL FEROZ", font=fuente(26, True),
           fill=(68, 240, 219))

    # Foto visible en aproximadamente 80 % del fotograma.
    y0 = int(h * (0.79 if formato == "largo" else 0.82))
    d.rounded_rectangle(
        (25, y0, w - 25, h - 43),
        radius=18, fill=(2, 11, 24, 198),
        outline=(56, 220, 215, 145), width=2,
    )
    texto = " ".join(escena["texto"].split()[:12])
    for tam in range(37 if formato == "largo" else 33, 21, -2):
        f = fuente(tam, True)
        lineas = partir_lineas(d, texto, f, w - 110)
        if len(lineas) <= 2:
            break
    for i, linea in enumerate(lineas[:2]):
        d.text((50, y0 + 15 + i * int(tam * 1.2)),
               linea, font=f, fill=(248, 251, 254))
    d.text((28, h - 28), "Imagen: " + credito[:58],
           font=fuente(14), fill=(237, 237, 237))
    final = Image.alpha_composite(fondo.convert("RGBA"), capa).convert("RGB")
    destino.parent.mkdir(parents=True, exist_ok=True)
    final.save(destino)
