"""Pruebas de miniaturas neon con capturas oficiales locales; cero red y cero YouTube."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from portadas_gta_neon import crear_portada_gta, elegir_foto, titular_breve


class TestPortadasNeon(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "tema_id": "gta6-raul-bautista",
            "portada_categoria": "raul",
            "portada_paleta": "amarillo",
            "visuales_preferidos": ["raul", "vice"],
        }

    def banco_falso(self, base):
        imagenes = base / "imagenes"
        imagenes.mkdir(parents=True)
        ruta = imagenes / "raul-prueba.jpg"
        Image.new("RGB", (1280, 720), (81, 135, 190)).save(ruta)
        (base / "catalogo.json").write_text(json.dumps({
            "origen": "https://www.rockstargames.com/VI/media/screenshots",
            "imagenes": [{"archivo": "imagenes/raul-prueba.jpg",
                          "categoria": "raul", "nombre": "Raul Bautista"}],
        }), encoding="utf-8")
        return ruta

    def test_titular_limitado_a_cinco_palabras(self):
        self.assertEqual(titular_breve("Raul: el atracador de Vice City"),
                         "RAUL: EL ATRACADOR DE VICE")
        self.assertEqual(titular_breve(""), "GTA VI")

    def test_selecciona_foto_oficial_sin_salir_de_banco(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "banco"
            ruta = self.banco_falso(base)
            self.assertEqual(elegir_foto(self.plan, base), ruta)
            (base / "catalogo.json").write_text(json.dumps({
                "origen": "https://dominio-no-oficial.example/img",
                "imagenes": [{"archivo": "imagenes/raul-prueba.jpg",
                              "categoria": "raul"}],
            }), encoding="utf-8")
            self.assertIsNone(elegir_foto(self.plan, base))

    def test_tres_portadas_llamativas_ligeras_y_diferentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "banco"
            self.banco_falso(base)
            huellas = set()
            for n in range(3):
                salida = Path(tmp) / ("miniatura_%d.jpg" % n)
                crear_portada_gta(self.plan, "RAUL: EL ATRACADOR",
                                  "largo", salida, variante=n, banco=base)
                self.assertLessEqual(salida.stat().st_size, 2_000_000)
                huellas.add(salida.read_bytes()[:2500])
                with Image.open(salida) as im:
                    self.assertEqual(im.size, (1280, 720))
                    self.assertEqual(im.mode, "RGB")
            self.assertEqual(len(huellas), 3)

    def test_vertical_sin_banco_con_fondo_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "vertical.jpg"
            crear_portada_gta(self.plan, "REAL DIMEZ", "short",
                              archivo, banco=Path(tmp)/"no-existe")
            with Image.open(archivo) as im:
                self.assertEqual(im.size, (720, 1280))
            self.assertLessEqual(archivo.stat().st_size, 2_000_000)


if __name__ == "__main__":
    unittest.main()
