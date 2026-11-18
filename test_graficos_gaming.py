"""Regresión para la nueva composición gaming-news sin recursos externos."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from graficos_gaming import tarjeta_gaming, palabras_destacadas
from motor_video import adaptar_escenas

class TestGamingNews(unittest.TestCase):
    def test_tarjeta_short_vertical(self):
        escena={"tipo":"gancho","texto":"Rockstar presenta novedades verificadas sobre el videojuego y sus personajes"}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"escena.png"
            tarjeta_gaming(escena,0,3,"Novedades GTA",out)
            self.assertTrue(out.exists())
            with Image.open(out) as im:
                self.assertEqual(im.size,(720,1280))
                self.assertEqual(im.format,"PNG")
    def test_texto_corto_jerarquia(self):
        texto=palabras_destacadas("Noticias oficiales sobre el estreno del videojuego")
        self.assertLessEqual(len(texto),35)
        self.assertTrue(texto)
    def test_short_fragmentado_para_cortes_frecuentes(self):
        texto=" ".join(["noticia"]*54)
        escenas=adaptar_escenas({"formato":"short","escenas":[{"tipo":"hecho_verificado","texto":texto}]})
        self.assertEqual(" ".join(x["texto"] for x in escenas),texto)
        self.assertEqual(len(escenas),3)

if __name__=="__main__":
    unittest.main()
