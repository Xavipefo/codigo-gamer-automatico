"""Validación real de tempo sin subir audio ni vídeo."""
import math
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

from audio_ritmo import ajustar_ritmo_wav, segundos_wav


class TestAudioRitmo(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg no disponible")
    def test_wav_conserva_tono_y_acelera_sin_desincronizar(self):
        import math
        from array import array
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "original.wav"
            frecuencia = 24000
            # Tono sintético 440 Hz durante 2 segundos.
            muestras = array(
                "h", (
                    int(8000 * math.sin(2 * math.pi * 440 * i / frecuencia))
                    for i in range(frecuencia * 2)
                )
            )
            with wave.open(str(ruta), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(frecuencia)
                audio.writeframes(muestras.tobytes())
            self.assertAlmostEqual(segundos_wav(ruta), 2.0, places=2)
            duracion = ajustar_ritmo_wav(ruta, 1.08)
            self.assertAlmostEqual(duracion, 2.0 / 1.08, delta=0.07)
            self.assertAlmostEqual(segundos_wav(ruta), duracion, places=2)
            with wave.open(str(ruta), "rb") as audio:
                self.assertEqual(audio.getframerate(), frecuencia)

    def test_ritmo_normal_no_altera_audio(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "a.wav"
            with wave.open(str(ruta), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(24000)
                audio.writeframes(bytes(48000))
            original = ruta.read_bytes()
            self.assertAlmostEqual(ajustar_ritmo_wav(ruta, 1.0), 1.0)
            self.assertEqual(ruta.read_bytes(), original)

    def test_impide_ritmos_excesivos(self):
        with self.assertRaises(ValueError):
            ajustar_ritmo_wav("nada.wav", 1.50)
        with self.assertRaises(ValueError):
            ajustar_ritmo_wav("nada.wav", math.nan)


if __name__ == "__main__":
    unittest.main()
