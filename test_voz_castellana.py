"""Comprobaciones sin peticiones de red para la voz castellana."""
import base64
import json
import unittest
from unittest.mock import patch

from voz_gemini_castellano import (
    ESTILO, MODEL, VOCES, MUESTRA, peticion_audio, extraer_audio,
)


class TestGeminiCastellano(unittest.TestCase):
    def test_espana_definida_en_el_estilo(self):
        self.assertIn("es-ES", ESTILO)
        self.assertIn("España", ESTILO)
        self.assertIn("castellano", ESTILO)
        self.assertIn("latinoamericano", ESTILO)

    def test_modelo_y_voces_validas(self):
        self.assertEqual(MODEL, "gemini-3.8-flash-tts")
        self.assertEqual(set(VOCES), {"Charon", "Achird"})

    def test_transcripcion_literal_separada_del_estilo(self):
        p = peticion_audio(MUESTRA, "Charon")
        self.assertEqual(p["model"], MODEL)
        contenido = p["input"][0]["content"][0]
        self.assertEqual(contenido["text"], MUESTRA)
        self.assertEqual(contenido["annotations"][0]["style"], ESTILO)
        self.assertEqual(p["response_format"]["mime_type"], "audio/wav")
        self.assertEqual(p["generation_config"]["speech_config"][0]["voice"], "Charon")


    def test_extrae_wav_desde_interactions_rest(self):
        wav_minimo = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 16
        ejemplo = {
            "steps": [
                {"type": "model_output",
                 "content": [{"type": "audio",
                              "mime_type": "audio/wav",
                              "data": base64.b64encode(wav_minimo).decode("ascii")}]}
            ]
        }
        self.assertEqual(extraer_audio(ejemplo), wav_minimo)

    def test_no_confunde_salidas_textuales_con_audio(self):
        ejemplo = {
            "steps": [
                {"type": "model_output",
                 "content": [{"type": "text", "text": "Hola"}]}
            ]
        }
        with self.assertRaises(RuntimeError):
            extraer_audio(ejemplo)

    def test_rechazar_voz_no_permitida(self):
        with self.assertRaises(ValueError):
            peticion_audio(MUESTRA, "VozInventada")

    def test_rechazar_texto_vacio(self):
        with self.assertRaises(ValueError):
            peticion_audio("", "Achird")


if __name__ == "__main__":
    unittest.main()
