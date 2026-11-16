"""Pruebas del reparto y render antes de cualquier publicación."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from motor_video import adaptar_escenas, resumen_visual
from voz_produccion import DEFAULT, NarradorGemini, elegir_voz, estimar_consumo


class TestRepartoNarradores(unittest.TestCase):
    def test_achird_en_shorts(self):
        self.assertEqual(elegir_voz("short"), "Achird")
        self.assertEqual(DEFAULT["short"], "Achird")

    def test_charon_en_analisis_largos(self):
        self.assertEqual(elegir_voz("largo"), "Charon")
        self.assertEqual(DEFAULT["largo"], "Charon")

    def test_rechaza_narrador_inventado(self):
        with self.assertRaises(ValueError):
            elegir_voz("short", {"narrador_voz": "Desconocido"})

    def test_plan_explicito_y_formato(self):
        self.assertEqual(
            elegir_voz("short", {"narrador_voz": "Achird", "formato": "short"}),
            "Achird",
        )
        with self.assertRaises(ValueError):
            elegir_voz("short", {"narrador_voz": "Charon", "formato": "largo"})

    def test_no_alterna_voces_dentro_del_video(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "clave-de-prueba"}):
            narrador = NarradorGemini(
                "short", {"formato": "short", "narrador_voz": "Achird"}
            )
            with tempfile.TemporaryDirectory() as t:
                with patch("voz_produccion.sintetizar", return_value=6.0) as call:
                    a = narrador.narrar("Este es un texto de demostración de voz.", Path(t) / "a.wav")
                    b = narrador.narrar("Este es el segundo texto de demostración.", Path(t) / "b.wav")
                    self.assertEqual(a + b, 12)
                    self.assertEqual(call.call_count, 2)
                    self.assertTrue(all(x.args[1] == "Achird" for x in call.call_args_list))

    def test_numero_de_peticiones_limitado(self):
        escenas = [{"tipo": "contexto", "texto": "Esta es una escena de prueba completa."}]*46
        with self.assertRaises(ValueError):
            estimar_consumo(escenas, "largo")

    def test_fragmentos_largos_reducen_solicitudes(self):
        texto = " ".join(["palabra"] * 160)
        plan = {"formato": "largo", "escenas": [{"tipo": "hecho_verificado", "texto": texto}]}
        escenas = adaptar_escenas(plan)
        self.assertEqual(len(escenas), 3)
        self.assertEqual(len(" ".join(x["texto"] for x in escenas).split()), 160)
        self.assertLessEqual(max(len(x["texto"].split()) for x in escenas), 75)
        self.assertTrue(all(len(x["texto"]) <= 1400 for x in escenas))

    def test_tarjeta_resume_pero_audio_conserva_original(self):
        texto = " ".join([f"palabra{i}" for i in range(60)])
        escena = {"tipo": "contexto", "texto": texto}
        vista = resumen_visual(escena, "largo")
        self.assertLess(len(vista["texto"]), len(escena["texto"]))
        self.assertEqual(escena["texto"], texto)
        self.assertTrue(vista["texto"].endswith("…"))


if __name__ == "__main__":
    unittest.main()
