#!/usr/bin/env python3
"""Prepara hasta cinco Shorts verificados de forma SECUENCIAL y PRIVADA.

Reutiliza una sola instalación de dependencias por lote (no reentrena
Qwen); cada Short se graba y confirma de manera independiente.
Si falla un vídeo, DETIENE el lote para no repetir subidas ni saltarse
una revisión de YouTube Studio.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from editorial import seleccionado

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "salida"
HISTORIAL = BASE / "historial_publicados.json"


def ejecutar(*args):
    subprocess.run(list(args), cwd=BASE, check=True, timeout=9000)


def comprobar_configuracion():
    if os.environ.get("PF_SUBIR_PRIVADO") != "SI":
        raise RuntimeError("El lote requiere subida exclusivamente PRIVADA")
    if not os.environ.get("YOUTUBE_OAUTH_JSON", "").strip():
        raise RuntimeError("Falta YOUTUBE_OAUTH_JSON en el entorno")
    if os.environ.get("PF_TTS_PROVIDER") != "qwen":
        raise RuntimeError("El lote sólo funciona con Ryan/Qwen local")


def estado_youtube():
    archivo = SALIDA / "youtube_resultado.json"
    if not archivo.exists():
        raise RuntimeError("No existe resultado de subida; no repetir a ciegas")
    registro = json.loads(archivo.read_text(encoding="utf-8"))
    if registro.get("estado") != "subido" or registro.get("privacidad_verificada") != "private":
        raise RuntimeError("YouTube no confirmó privacidad de la subida")
    return registro


def registrar_y_guardar(video):
    ejecutar(sys.executable, "registrar_subida.py")
    ejecutar("git", "add", "historial_publicados.json")
    ejecutar("git", "commit", "-m", "chore: registrar Short PRIVADO " + video["tema_id"])
    ejecutar("git", "push")
    print("Registrado en GitHub sin duplicar:", video["tema_id"], flush=True)


def producir(cantidad, lanzar=ejecutar):
    cantidad = int(cantidad)
    if not 1 <= cantidad <= 5:
        raise ValueError("El lote solo admite de uno a cinco Shorts")
    comprobar_configuracion()
    resultados = []
    for indice in range(cantidad):
        # Busca la próxima noticia confirmada que NO figure ya subida.
        tema = seleccionado("", "short")
        print(
            f"PREPARANDO {indice+1}/{cantidad}: {tema['id']} (SOLO PRIVADO)",
            flush=True,
        )
        if SALIDA.exists():
            shutil.rmtree(SALIDA)
        lanzar(sys.executable, "editorial.py", "--formato", "short",
               "--tema", tema["id"])
        lanzar(sys.executable, "generar_guion_ia.py", "--formato", "short")
        lanzar(sys.executable, "motor_video.py")
        lanzar(sys.executable, "control_calidad.py", "--formato", "short")
        # Guardar imágenes y mosaico POR TEMA antes de eliminar SALIDA en el
        # siguiente vídeo; nunca copiar MP4, narraciones o secretos.
        revision = SALIDA / "revision_visual"
        if revision.is_dir():
            destino_revision = BASE / "lote_revision" / tema["id"]
            if destino_revision.exists():
                shutil.rmtree(destino_revision)
            shutil.copytree(revision, destino_revision)
        # Este es el único paso externo irreversible: subida PRIVADA.
        # Si falla no reintentar: revisar el ID en YouTube Studio.
        lanzar(sys.executable, "subir_youtube_privado.py", "--formato", "short")
        resultado = estado_youtube()
        if resultado["tema_id"] != tema["id"]:
            raise RuntimeError("Resultado de subida no coincide con tema")
        # Registrar y hacer push por CADA vídeo, no al final del lote.
        # Así un fallo posterior no pierde los IDs privados ya subidos.
        registrar_y_guardar(resultado)
        resultados.append(resultado["video_id"])
        if resultado.get("miniatura_confirmada") is not True:
            raise RuntimeError(
                "Short privado guardado, pero la miniatura necesita revisión: "
                + resultado["video_id"]
            )
    print("Lote completado: ", len(resultados), "Shorts privados verificados.")
    print("IDs de vídeos (ninguno público):", ", ".join(resultados))
    return resultados


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cantidad", type=int, default=2)
    args = parser.parse_args()
    producir(args.cantidad)


if __name__ == "__main__":
    main()
