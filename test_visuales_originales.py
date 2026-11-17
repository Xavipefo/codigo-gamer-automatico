"""Verifica que hay ilustraciones editoriales sin dependencias externas."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from visuales_originales import crear_banco_original, CREDITO

class BancoOriginalTest(unittest.TestCase):
    def test_genera_seis_fondos_distintos(self):
        with tempfile.TemporaryDirectory() as td:
            recursos = crear_banco_original("gta6-vice-city", td)
            self.assertEqual(len(recursos), 6)
            datos = set()
            for ruta, credito in recursos:
                self.assertEqual(credito, CREDITO)
                self.assertTrue(Path(ruta).is_file())
                with Image.open(ruta) as imagen:
                    self.assertEqual(imagen.size, (1280, 720))
                datos.add(Path(ruta).read_bytes())
            self.assertEqual(len(datos), 6)

    def test_resultado_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            uno = crear_banco_original("tema-estable", a, cantidad=2)
            dos = crear_banco_original("tema-estable", b, cantidad=2)
            self.assertEqual([x[0].read_bytes() for x in uno],
                             [x[0].read_bytes() for x in dos])

if __name__ == "__main__":
    unittest.main()
