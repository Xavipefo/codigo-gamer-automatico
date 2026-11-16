import copy
import unittest
from pathlib import Path

from preparar_contenido import cargar_temas, comprobar_enlace, preparar, validar_tema


class TestPreparacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temas = cargar_temas(Path(__file__).with_name("temas_verificados.json"))

    def test_dos_temas_validos(self):
        self.assertGreaterEqual(len(self.temas), 2)

    def test_dominios(self):
        self.assertTrue(comprobar_enlace("https://www.rockstargames.com/newswire/"))
        self.assertFalse(comprobar_enlace("http://www.rockstargames.com/"))
        self.assertFalse(comprobar_enlace("https://rockstargames.com.ejemplo.com/"))
        self.assertFalse(comprobar_enlace("https://example.com/"))

    def test_guion_y_plan_pendientes_de_revision(self):
        guion, descripcion, plan = preparar(self.temas[0])
        self.assertGreater(len(guion.split()), 30)
        self.assertIn("https://", descripcion)
        self.assertEqual(plan["estado"], "BORRADOR_PENDIENTE_REVISION")
        self.assertFalse(plan["publicacion_automatica"])

    def test_fuente_no_valida_bloqueada(self):
        tema = copy.deepcopy(self.temas[0])
        tema["hechos"][0]["fuente"] = "https://un-sitio-desconocido.com/falso"
        with self.assertRaises(ValueError):
            validar_tema(tema)

    def test_tema_no_confirmado_bloqueado(self):
        tema = copy.deepcopy(self.temas[0])
        tema["estado"] = "rumor"
        with self.assertRaises(ValueError):
            validar_tema(tema)


if __name__ == "__main__":
    unittest.main()
