"""Tests sin red ni modelos para el motor de voz y material visual."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voz_natural import VOCES, ARCHIVOS, pronunciacion
from video_material import descargar_clip, url_segura


class TestVozNatural(unittest.TestCase):
    def test_voces_espanolas(self):
        self.assertTrue({"em_alex", "em_santa", "ef_dora"}.issubset(VOCES))
        self.assertEqual(len(ARCHIVOS), 2)
        self.assertTrue(all(len(huella) == 64 for huella in ARCHIVOS.values()))

    def test_pronunciacion_videojuegos(self):
        texto = pronunciacion("GTA VI llega a PS5 con 30 FPS y 212 GB")
        self.assertIn("G T A seis", texto)
        self.assertIn("PlayStation cinco", texto)
        self.assertIn("fotogramas por segundo", texto)
        self.assertIn("gigabytes", texto)


class TestMaterialVisual(unittest.TestCase):
    def test_no_descarga_si_no_hay_secreto(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(
                descargar_clip("gta6-lanzamiento-oficial",
                               Path(tempfile.gettempdir()) / "no_clip_pf.mp4")
            )

    def test_bloquea_plataformas_y_red_local(self):
        for url in (
            "http://files.example.com/clip.mp4",
            "https://youtube.com/video.mp4",
            "https://www.rockstargames.com/video.mp4",
            "https://127.0.0.1/clip.mp4",
        ):
            with self.assertRaises(ValueError):
                url_segura(url)

    def test_acepta_servidor_global_y_mp4_directo(self):
        dns = [(0, 0, 0, "", ("8.8.8.8", 443))]
        with patch("socket.getaddrinfo", return_value=dns):
            self.assertEqual(
                url_segura("https://media.example.net/original.mp4"),
                "https://media.example.net/original.mp4"
            )

    def test_exige_derechos_confirmados(self):
        config = '{"gta6-lanzamiento-oficial":{"url":"https://media.example.net/clip.mp4"}}'
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"PF_CLIPS_JSON": config}
        ):
            with self.assertRaises(ValueError):
                descargar_clip("gta6-lanzamiento-oficial", Path(temp) / "clip.mp4")


if __name__ == "__main__":
    unittest.main()
