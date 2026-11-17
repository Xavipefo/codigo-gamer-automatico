"""Pruebas de selección segura de Qwen3-TTS sin descargar modelos ni usar red."""
import unittest
from pathlib import Path

from voz_qwen_libre import MODELOS, PERFILES, PRESET, TEXTO, configurar, generar


class TestQwenLibre(unittest.TestCase):
    def test_solo_pesos_oficiales(self):
        self.assertEqual(
            MODELOS["ligero"],
            "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        )
        self.assertEqual(
            MODELOS["diseno"],
            "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        )

    def test_perfiles_originales_de_espana(self):
        self.assertIn("Castilian Spanish", PERFILES["presentador"])
        self.assertIn("from Spain", PERFILES["analista"])
        self.assertIn("No Latin American accent", PERFILES["presentador"])
        self.assertIn("No Latin American accent", PERFILES["analista"])
        self.assertIn("Do not imitate", PERFILES["presentador"])

    def test_presets_dos_voces_masculinas(self):
        self.assertEqual(PRESET, {"presentador": "Ryan", "analista": "Aiden"})
        self.assertIn("Píxel Feroz", TEXTO)

    def test_rechaza_modelos_y_perfiles_no_autorizados(self):
        with self.assertRaises(ValueError):
            configurar("../modelo_desconocido", "presentador", Path("a.wav"))
        with self.assertRaises(ValueError):
            configurar("ligero", "voz_ajena", Path("a.wav"))
        with self.assertRaises(ValueError):
            configurar("ligero", "presentador", Path("a.mp3"))

    def test_no_generar_si_no_se_carga_modelo(self):
        with self.assertRaisesRegex(ValueError, "motor local"):
            generar("ligero", "presentador", Path("a.wav"), motor=None)


if __name__ == "__main__":
    unittest.main()
