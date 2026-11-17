"""Rechazar vídeos largos sin recursos reales antes de gastar CPU."""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

import validar_banco_visual
from voz_qwen_produccion import NarradorQwen


class TestVisualPrevio(unittest.TestCase):
    def test_no_hay_clips_ni_imagenes(self):
        with patch.object(validar_banco_visual, "catalogo_clips", return_value=[]):
            with patch.object(validar_banco_visual, "catalogo", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "BLOQUEO DE CALIDAD"):
                    validar_banco_visual.validar("tema-ficticio")

    def test_exige_ambos_tipos(self):
        with patch.object(validar_banco_visual, "catalogo_clips", return_value=[1]):
            with patch.object(validar_banco_visual, "catalogo", return_value=[]):
                with self.assertRaisesRegex(RuntimeError, "PF_IMAGENES_JSON"):
                    validar_banco_visual.validar("tema-ficticio")

    def test_valida_con_clips_e_imagenes_autorizados(self):
        with patch.object(validar_banco_visual, "catalogo_clips", return_value=[1, 2]):
            with patch.object(validar_banco_visual, "catalogo", return_value=[1, 2, 3]):
                self.assertEqual(validar_banco_visual.validar("tema-prueba"), (2, 3))

    def test_ryan_nueva_velocidad_solo_en_largos(self):
        with patch.dict(os.environ, {"PF_TTS_PROVIDER":"qwen"}):
            largo = NarradorQwen(
                "largo", {"formato":"largo", "narrador_voz":"Ryan"},
                motor=MagicMock()
            )
            short = NarradorQwen(
                "short", {"formato":"short", "narrador_voz":"Ryan"},
                motor=MagicMock()
            )
        self.assertEqual(largo.factor_ritmo, 1.10)
        self.assertEqual(short.factor_ritmo, 1.0)


if __name__ == "__main__":
    unittest.main()
