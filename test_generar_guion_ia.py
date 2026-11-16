"""Test de guiones IA: sin red ni secretos."""
import unittest
from generar_guion_ia import (
    cifras, hechos_permitidos, construir_prompt, normalizar_escenas
)
from preparar_contenido import CTA_SUSCRIPCION


TEMA = {
    "id": "test-gta6",
    "titulo": "GTA VI: lanzamiento oficial",
    "gancho": "¿Qué sabemos sobre GTA VI?",
    "contexto": "Rockstar ha hecho anuncios oficiales.",
    "hechos": [
        {"texto": "GTA VI llegará el 19 de noviembre de 2026",
         "fuente": "https://www.rockstargames.com/VI"},
        {"texto": "El juego llegará a PlayStation 5",
         "fuente": "https://www.rockstargames.com/VI"},
        {"texto": "La historia transcurre en Leonida",
         "fuente": "https://www.rockstargames.com/VI"},
    ],
}


class TestsGuionIA(unittest.TestCase):
    def test_cifras_controladas(self):
        self.assertIn("2026", cifras(hechos_permitidos(TEMA)))

    def test_prompt_usa_hechos(self):
        prompt = construir_prompt(TEMA, "short")
        self.assertIn("19 de noviembre", prompt)
        self.assertIn("ÚNICOS HECHOS", prompt)
        self.assertIn(CTA_SUSCRIPCION, prompt)

    def test_no_acepta_cifras_inventadas(self):
        frase = ("Rockstar ha confirmado GTA VI para "
                 "2029 con varias novedades verificadas. " * 9)
        with self.assertRaises(ValueError):
            normalizar_escenas([frase] * 5, TEMA, "short")

    def test_cta_obligatoria(self):
        escenas = [
            ("Rockstar explica GTA VI y su lanzamiento. " * 3).strip(),
            ("Rockstar explica la historia y el escenario del juego. " * 3).strip(),
            ("Rockstar presenta lo confirmado hasta ahora. " * 3).strip(),
            ("La información oficial es la referencia principal. " * 3).strip(),
            ("Seguiremos las novedades del mundo de los videojuegos. " * 2).strip(),
        ]
        normalizadas, guion = normalizar_escenas(escenas, TEMA, "short")
        self.assertIn(CTA_SUSCRIPCION, normalizadas[-1]["texto"])
        self.assertEqual(guion.count(CTA_SUSCRIPCION), 1)


if __name__ == "__main__":
    unittest.main()
