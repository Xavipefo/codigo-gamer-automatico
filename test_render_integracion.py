"""Prueba de montaje REAL con FFmpeg, sin Gemini ni YouTube.

Reproduce un vídeo largo con fallo HTTP 429 a mitad del proceso y verifica
que el segundo intento EN EL MISMO RUNNER retoma WAV/MP4 anteriores. El
contenido y sus pistas sintéticas no salen de GitHub Actions.
"""
import hashlib
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import motor_video
from voz_gemini_castellano import TTSRateLimitError


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "La integración audiovisual requiere ffmpeg y ffprobe")
class TestIntegracionFFmpeg(unittest.TestCase):
    def test_render_real_reanuda_audio_y_mp4_tras_429(self):
        escenas = [
            {
                "tipo": "gancho",
                "texto": "En este reportaje vamos a explicar lo que conocemos "
                         "oficialmente sobre los protagonistas de GTA seis "
                         "y el mundo en el que tiene lugar la historia."
            },
            {
                "tipo": "cierre",
                "texto": "La información confirmada es nuestro punto de partida "
                         "para investigar sin difundir rumores sobre los "
                         "videojuegos más importantes de los próximos meses."
            },
        ]
        guion = " ".join(x["texto"] for x in escenas)
        plan = {
            "canal": "Píxel Feroz",
            "tema_id": "integracion-gta6",
            "estado": "BORRADOR_PENDIENTE_REVISION",
            "publicacion_automatica": False,
            "formato": "largo",
            "narrador_voz": "Charon",
            "titulo_propuesto": "GTA VI: lo que sabemos del nuevo juego",
            "texto_miniatura": "GTA VI: claves confirmadas",
            "huella_guion": hashlib.sha256(guion.encode("utf-8")).hexdigest(),
            "escenas": escenas,
        }

        llamadas = []
        def audio_falso(texto, voz, ruta):
            llamadas.append((texto, voz))
            if len(llamadas) == 2:
                raise TTSRateLimitError("HTTP 429 de prueba")
            destino = Path(ruta)
            destino.parent.mkdir(parents=True, exist_ok=True)
            with wave.open(str(destino), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(bytes(24000 * 2 * 6))
            return 6.0

        checkpoint = (
            Path(tempfile.gettempdir()) /
            ("pixel_feroz_render_" + plan["huella_guion"][:20] + "_charon")
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "salida"
                with patch.object(motor_video, "SALIDA", out), patch.dict(
                    os.environ, {"GEMINI_API_KEY": "clave-de-prueba", "PF_TTS_PROVIDER": "gemini"}
                ), patch(
                    "voz_produccion.sintetizar", side_effect=audio_falso
                ), patch(
                    "voz_produccion.time.sleep"
                ), patch(
                    "motor_video.descargar_clip", return_value=None
                ):
                    with self.assertRaises(TTSRateLimitError):
                        motor_video.montar(plan, guion)
                    wav = checkpoint / "audio_000.wav"
                    mp4 = checkpoint / "clip_000.mp4"
                    self.assertTrue(wav.is_file())
                    self.assertTrue(mp4.is_file())
                    primera_marca = mp4.stat().st_mtime_ns

                    # El segundo intento no puede repetir la voz/clip 000.
                    motor_video.montar(plan, guion)
                    final = out / "pixel_feroz_largo.mp4"
                    self.assertGreater(final.stat().st_size, 20000)
                    self.assertTrue((out / "miniatura.jpg").is_file())
                    self.assertEqual(len(llamadas), 3)
                    self.assertEqual([x[1] for x in llamadas],
                                     ["Charon", "Charon", "Charon"])
                    # Tras completar, el checkpoint del runner se limpia.
                    self.assertFalse(checkpoint.exists())
        finally:
            shutil.rmtree(checkpoint, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
