"""Pruebas de Azure TTS sin red, claves reales ni gastos."""
import io
import os
import tempfile
import unittest
import urllib.error
import wave
from pathlib import Path
from unittest.mock import patch

from voz_azure_castellano import MUESTRA, VOCES, crear_ssml, sintetizar, validar_region


class TestVocesAzure(unittest.TestCase):
    def test_dos_voces_de_espana(self):
        self.assertEqual(VOCES["Alvaro"], "es-ES-AlvaroNeural")
        self.assertEqual(VOCES["Arnau"], "es-ES-ArnauNeural")

    def test_ssml_no_permite_inyeccion_xml(self):
        texto = 'Oye, GTA VI & sus cambios <extra> son "importantes".'
        ssml = crear_ssml(texto, "Alvaro")
        self.assertIn("es-ES-AlvaroNeural", ssml)
        self.assertIn("GTA VI &amp; sus cambios &lt;extra&gt;", ssml)
        self.assertNotIn("<extra>", ssml)

    def test_region_validada_antes_de_crear_url(self):
        self.assertEqual(validar_region("westeurope"), "westeurope")
        with self.assertRaises(ValueError):
            validar_region("https://servidor-inseguro.invalid/")
        with self.assertRaises(ValueError):
            validar_region("")

    def test_rechaza_voz_y_texto_no_validos(self):
        with self.assertRaises(ValueError):
            crear_ssml(MUESTRA, "Charon")
        with self.assertRaises(ValueError):
            crear_ssml("x", "Arnau")

    def test_peticion_rest_azure_espanola_y_wav_valido(self):
        salida = io.BytesIO()
        with wave.open(salida, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(bytes(24000 * 2 * 5))
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "arnau.wav"
            with patch(
                "voz_azure_castellano.urllib.request.urlopen",
                return_value=io.BytesIO(salida.getvalue()),
            ) as pedir:
                segundos = sintetizar(
                    "Esto es una prueba de acento español para Píxel Feroz.",
                    "Arnau", ruta, clave="simulacion", region="westeurope"
                )
            self.assertEqual(segundos, 5.0)
            self.assertTrue(ruta.exists())
            pedido = pedir.call_args.args[0]
            self.assertEqual(
                pedido.full_url,
                "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1",
            )
            self.assertEqual(pedido.get_header("Ocp-apim-subscription-key"), "simulacion")
            self.assertEqual(
                pedido.get_header("X-microsoft-outputformat"),
                "riff-24khz-16bit-mono-pcm",
            )

    def test_falla_sin_guardar_archivo_ni_exponer_clave(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "error.wav"
            error = urllib.error.HTTPError("https://test", 429, "rate", {}, None)
            with patch(
                "voz_azure_castellano.urllib.request.urlopen",
                side_effect=error
            ):
                with self.assertRaisesRegex(RuntimeError, "HTTP 429") as exc:
                    sintetizar(
                        MUESTRA, "Alvaro", ruta, clave="secreto-super-privado",
                        region="westeurope"
                    )
            self.assertNotIn("secreto-super-privado", str(exc.exception))
            self.assertFalse(ruta.exists())


if __name__ == "__main__":
    unittest.main()
