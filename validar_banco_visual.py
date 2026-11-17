#!/usr/bin/env python3
"""Evita gastar 60-90 minutos en un largo que volvería a ser solo texto.

No descarga clips ni imprime URLs privadas: comprueba permisos/estructura
de los secretos y requiere al menos un vídeo y una imagen autorizados.
"""
import argparse

from editorial import seleccionado
from video_material import catalogo_clips
from visuales_autorizados import catalogo


def validar(tema_id):
    clips = catalogo_clips(tema_id)
    fotos = catalogo(tema_id)
    if not clips or not fotos:
        faltan = (
            ("PF_CLIPS_JSON " if not clips else "")
            + ("PF_IMAGENES_JSON" if not fotos else "")
        ).strip()
        raise RuntimeError(
            "BLOQUEO DE CALIDAD: el vídeo largo solicita imágenes Y clips "
            "con derechos confirmados, pero faltan recursos para "
            + tema_id + ": " + faltan
            + ". Se detiene ANTES de generar narración, montar o subir. "
            "Añade los manifests legítimos a GitHub Secrets o marca "
            "'permitir_solo_graficos' en la ejecución de largo."
        )
    print(
        "Banco multimedia listo para", tema_id,
        "| clips autorizados:", len(clips),
        "| imágenes autorizadas:", len(fotos),
        "| sin descargas ni publicación",
        flush=True,
    )
    return len(clips), len(fotos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tema", default="")
    args = parser.parse_args()
    elegido = seleccionado(args.tema, "largo")
    validar(elegido["id"])


if __name__ == "__main__":
    main()
