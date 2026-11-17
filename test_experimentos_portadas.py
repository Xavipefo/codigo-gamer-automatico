"""Tres titulares y portadas A/B sin APIs, renders ni publicaciones."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from experimentos_portadas import crear_portada, generar, titulos_originales


class TestExperimentos(unittest.TestCase):
    def setUp(self):
        self.tema = {
            "id": "gta6-analisis",
            "titulo": "GTA VI: Jason y Lucia",
            "texto_miniatura": "JASON Y LUCIA",
            "gancho": "Por qué Jason y Lucia son protagonistas en Leonida",
        }
        self.plan = {
            "tema_id": self.tema["id"],
            "formato": "largo",
            "titulo_propuesto": self.tema["titulo"],
        }

    def test_tres_titulos_sin_inventar_cifras(self):
        titulos = titulos_originales(self.plan, self.tema)
        self.assertEqual(len(titulos), 3)
        self.assertEqual(len(set(titulos)), 3)
        self.assertTrue(all(len(s) <= 100 for s in titulos))

    def test_solo_tres_alternativas_originales(self):
        self.tema["titulos_experimento"] = ["UNO", "DOS", "TRES"]
        with self.assertRaises(ValueError):
            titulos_originales(self.plan, self.tema)
        self.tema["titulos_experimento"] = ["Versión A confirmada"] * 3
        with self.assertRaises(ValueError):
            titulos_originales(self.plan, self.tema)

    def test_exporta_imagenes_diferentes_y_json(self):
        with tempfile.TemporaryDirectory() as t:
            carpeta = Path(t) / "portadas"
            resultado = generar(self.plan, self.tema, carpeta)
            archivos = [carpeta / f"miniatura_{x}.jpg" for x in "abc"]
            self.assertEqual(len(resultado["variantes"]), 3)
            self.assertTrue(all(f.is_file() for f in archivos))
            muestras = []
            for archivo in archivos:
                with Image.open(archivo) as im:
                    self.assertEqual(im.size, (1280, 720))
                    muestras.append(im.getpixel((10,10)))
            self.assertEqual(len(set(muestras)), 3)
            self.assertEqual(
                json.loads((carpeta/"experimento.json").read_text())["estado"],
                "REVISAR_MANUALMENTE"
            )
            self.assertFalse(resultado["experimentacion_automatica"])

    def test_shorts_no_activan_experimento(self):
        with tempfile.TemporaryDirectory() as t:
            self.plan["formato"] = "short"
            datos = generar(self.plan, self.tema, Path(t))
            self.assertIn("Shorts", datos["nota"])
            with Image.open(Path(t)/"miniatura_a.jpg") as im:
                self.assertEqual(im.size, (720, 1280))


if __name__ == "__main__":
    unittest.main()
