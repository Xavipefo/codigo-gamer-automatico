"""Ryan real para vídeos privados: pruebas sin descargar Qwen ni usar API."""
import os
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

from voz_produccion import elegir_voz
from voz_qwen_produccion import NarradorQwen, MODELO_LOCAL, VOZ_LOCAL


class TestQwenProduccion(unittest.TestCase):
    def test_qwen_asigna_ryan_a_ambos_formatos(self):
        with patch.dict(os.environ, {"PF_TTS_PROVIDER": "qwen"}):
            self.assertEqual(elegir_voz("short"), "Ryan")
            self.assertEqual(elegir_voz("largo"), "Ryan")
        self.assertEqual(VOZ_LOCAL, "Ryan")
        self.assertIn("0.6B-CustomVoice", MODELO_LOCAL)

    def test_ryan_es_voz_principal_sin_forzar_variable(self):
        with patch.dict(os.environ, {"PF_TTS_PROVIDER": ""}):
            self.assertEqual(elegir_voz("short"), "Ryan")
            self.assertEqual(elegir_voz("largo"), "Ryan")

    def test_qwen_no_necesita_credenciales_de_tts(self):
        motor = MagicMock()
        with patch.dict(os.environ, {
            "PF_TTS_PROVIDER": "qwen",
            "GEMINI_API_KEY": "",
            "AZURE_SPEECH_KEY": "",
        }):
            narrador = NarradorQwen(
                "short",
                {"formato": "short", "narrador_voz": "Ryan"},
                motor=motor,
            )
        self.assertEqual(narrador.proveedor, "qwen")
        self.assertEqual(narrador.voz_real, "Qwen3-TTS 0.6B / Ryan")

    def test_rechaza_voz_de_analista_descartada(self):
        with patch.dict(os.environ, {"PF_TTS_PROVIDER": "qwen"}):
            with self.assertRaises(ValueError):
                NarradorQwen(
                    "largo",
                    {"formato": "largo", "narrador_voz": "Aiden"},
                    motor=MagicMock(),
                )

    def test_qwen_sintetiza_y_reutiliza_wav_privado(self):
        try:
            import numpy as np
            import soundfile
        except ImportError:
            self.skipTest("numpy y soundfile no instalados en este entorno")
        motor = MagicMock()
        motor.generate_custom_voice.return_value = (
            [np.zeros(24000 * 8, dtype=np.float32)], 24000
        )
        texto = "Una noticia original y verificada sobre videojuegos para Píxel Feroz."
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ, {"PF_TTS_PROVIDER": "qwen"}
        ):
            destino = Path(tmp) / "voz_000.wav"
            narrador = NarradorQwen(
                "short",
                {"formato": "short", "narrador_voz": "Ryan"},
                motor=motor,
            )
            duracion = narrador.narrar(texto, destino)
            self.assertEqual(duracion, 8.0)
            with wave.open(str(destino), "rb") as wf:
                self.assertEqual(wf.getnchannels(), 1)
                self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(
                motor.generate_custom_voice.call_args.kwargs["speaker"], "Ryan"
            )
            recuperada = narrador.narrar(texto, destino)
            self.assertEqual(recuperada, 8.0)
            self.assertEqual(motor.generate_custom_voice.call_count, 1)
            self.assertEqual(narrador.recuperados, 1)


if __name__ == "__main__":
    unittest.main()
