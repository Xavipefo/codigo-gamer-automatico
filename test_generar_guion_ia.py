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

    def test_largo_1053_palabras_y_ocho_escenas_es_recuperable(self):
        # Caso real observado: 1053 palabras y una estructura fuera de rango.
        escena = ("Rockstar ha presentado Leonida y sus regiones oficialmente. " * 15).strip()
        originales = [escena for _ in range(8)]
        hechos_antes = " ".join(originales)
        normalizadas, guion = normalizar_escenas(originales, TEMA, "largo")
        self.assertEqual(len(normalizadas), 9)
        self.assertEqual(guion.count(CTA_SUSCRIPCION), 1)
        self.assertTrue(guion.endswith(CTA_SUSCRIPCION))
        self.assertEqual(
            " ".join(guion.replace(CTA_SUSCRIPCION, "").split()),
            " ".join(hechos_antes.split())
        )

    def test_largo_con_doce_escenas_conserva_texto(self):
        escena = ("Rockstar sitúa la historia en Leonida oficialmente. " * 14).strip()
        originales = [escena for _ in range(12)]
        normalizadas, guion = normalizar_escenas(originales, TEMA, "largo")
        self.assertEqual(len(normalizadas), 9)
        self.assertEqual(
            " ".join(guion.replace(CTA_SUSCRIPCION, "").split()),
            " ".join(" ".join(originales).split())
        )

    def test_largo_realmente_corto_sigue_bloqueado(self):
        escena = ("Rockstar confirma la historia en Leonida. " * 8).strip()
        with self.assertRaisesRegex(ValueError, "fuera"):
            normalizar_escenas([escena] * 9, TEMA, "largo")

    def test_largo_cifras_inventadas_siguen_bloqueadas(self):
        escena = ("Rockstar ha presentado 999 regiones en Leonida oficialmente. " * 17).strip()
        with self.assertRaisesRegex(ValueError, "cifras no verificadas"):
            normalizar_escenas([escena] * 9, TEMA, "largo")

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
