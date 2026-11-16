#!/usr/bin/env python3
"""Narración local española con Kokoro 82M (ONNX / Apache-2.0).

Carga una sola vez los pesos para todas las escenas del vídeo. Descarga solo
de la publicación oficial fijada y verifica SHA-256 antes de ejecutarlos.
No realiza peticiones de síntesis de voz a servicios externos.
"""
import hashlib
import json
import os
import re
import tempfile
import urllib.request
import wave
from pathlib import Path

BASE = Path(__file__).resolve().parent
VOZ = BASE / "voz" / "kokoro"
ORIGEN = (
    "https://github.com/thewh1teagle/kokoro-onnx/"
    "releases/download/model-files-v1.1/"
)
ARCHIVOS = {
    "kokoro-v1.0.int8.onnx": (
        "ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c"
    ),
    "voices-v1.0.bin": (
        "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d"
    ),
}
VOCES = {"em_alex", "em_santa", "ef_dora"}
CONFIG_VOZ = BASE / "config.json"


def huella_archivo(ruta):
    suma = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            suma.update(bloque)
    return suma.hexdigest()


def asegurar_modelo():
    VOZ.mkdir(parents=True, exist_ok=True)
    for nombre, digest in ARCHIVOS.items():
        destino = VOZ / nombre
        if destino.is_file() and huella_archivo(destino) == digest:
            continue
        if destino.exists():
            destino.unlink()
        temporal = destino.with_suffix(destino.suffix + ".part")
        try:
            peticion = urllib.request.Request(
                ORIGEN + nombre,
                headers={"User-Agent": "PixelFerozVoice/1.0"},
            )
            with urllib.request.urlopen(peticion, timeout=120) as respuesta:
                with temporal.open("wb") as salida:
                    while True:
                        bloque = respuesta.read(1024 * 1024)
                        if not bloque:
                            break
                        salida.write(bloque)
                        if salida.tell() > 150_000_000:
                            raise RuntimeError("El archivo de Kokoro excede 150 MB")
            if huella_archivo(temporal) != digest:
                raise RuntimeError("La firma SHA-256 del modelo Kokoro no coincide")
            temporal.replace(destino)
            print("Voz Kokoro descargada y comprobada:", nombre, flush=True)
        finally:
            temporal.unlink(missing_ok=True)
    return VOZ / "kokoro-v1.0.int8.onnx", VOZ / "voices-v1.0.bin"


def pronunciacion(texto):
    """Normaliza algunas siglas habituales para la locución en castellano."""
    texto = re.sub(r"\bGTA\s*VI\b", "G T A seis", texto, flags=re.I)
    texto = re.sub(r"\bGTA\b", "G T A", texto, flags=re.I)
    texto = re.sub(r"\bPS5\b", "PlayStation cinco", texto, flags=re.I)
    texto = re.sub(r"\bFPS\b", "fotogramas por segundo", texto, flags=re.I)
    texto = re.sub(r"\bGB\b", "gigabytes", texto, flags=re.I)
    return texto


class NarradorKokoro:
    def __init__(self, voz=None, velocidad=None):
        from kokoro_onnx import Kokoro
        modelo, estilos = asegurar_modelo()
        configuracion = json.loads(CONFIG_VOZ.read_text(encoding="utf-8"))
        self.voz = voz or configuracion.get("voz_nombre", "em_alex")
        if self.voz not in VOCES:
            raise ValueError("La voz solicitada no existe o no es española")
        self.velocidad = float(
            velocidad if velocidad is not None
            else configuracion.get("voz_velocidad", 1.02)
        )
        if not 0.85 <= self.velocidad <= 1.15:
            raise ValueError("Velocidad no válida")
        self.modelo = Kokoro(str(modelo), str(estilos))
        print(
            "Motor de voz: Kokoro ONNX | español |",
            self.voz, "| velocidad", self.velocidad, flush=True
        )

    def narrar(self, texto, destino):
        import soundfile as sf
        if not texto or not texto.strip():
            raise ValueError("No se puede narrar un texto vacío")
        audio, sample_rate = self.modelo.create(
            pronunciacion(texto),
            voice=self.voz,
            speed=self.velocidad,
            lang="es",
        )
        if len(audio) < int(sample_rate * .2):
            raise RuntimeError("Kokoro produjo una narración demasiado corta")
        destino.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(destino), audio, sample_rate, subtype="PCM_16")
        with wave.open(str(destino), "rb") as entrada:
            duracion = entrada.getnframes() / entrada.getframerate()
        if not .2 <= duracion <= 180:
            raise RuntimeError("Duración de voz fuera de rango")
        return duracion


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--probar", action="store_true")
    parser.add_argument("--voz", default="em_alex", choices=sorted(VOCES))
    parser.add_argument("--salida", type=Path, default=None)
    args = parser.parse_args()
    if not args.probar:
        parser.error("Solo se permite --probar; el montaje llama a NarradorKokoro")
    narrador = NarradorKokoro(voz=args.voz)
    with tempfile.TemporaryDirectory(prefix="pf_voz_") as carpeta:
        ruta = args.salida or Path(carpeta) / "prueba.wav"
        segundos = narrador.narrar(
            "¡Atención, amantes de los videojuegos! "
            "Píxel Feroz te cuenta las novedades de GTA seis y mucho más. "
            "Suscríbete para estar al día.",
            ruta,
        )
        print("VOZ KOKORO OK, segundos:", round(segundos, 2))
        print("Voz:", args.voz)
        print("Prueba sin vídeo ni subida a YouTube.")


if __name__ == "__main__":
    main()
