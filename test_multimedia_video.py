"""Prueba real: mezclar clips autorizados, imágenes y Ryan simulado SIN APIs."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from motor_video import seleccionar_medio
from video_material import catalogo_clips, creditos_clips


class TestMixVisual(unittest.TestCase):
    def test_prioridad_y_rotacion(self):
        self.assertEqual(seleccionar_medio(0, "gancho", 3, 4), "clip")
        self.assertEqual(seleccionar_medio(1, "hecho_verificado", 3, 4), "foto")
        self.assertEqual(seleccionar_medio(2, "hecho_verificado", 3, 4), "clip")
        self.assertEqual(seleccionar_medio(3, "hecho_verificado", 3, 4), "foto")
        self.assertEqual(seleccionar_medio(4, "hecho_verificado", 3, 4), "clip")
        self.assertEqual(seleccionar_medio(5, "cierre", 3, 4), "tarjeta")
        self.assertEqual(seleccionar_medio(1, "hecho_verificado", 1, 0), "clip")
        self.assertEqual(seleccionar_medio(1, "hecho_verificado", 0, 2), "foto")
        self.assertEqual(seleccionar_medio(1, "hecho_verificado", 0, 0), "tarjeta")

    def test_manifiesto_multiclips_y_creditos(self):
        clips = [
            {"url":"https://cdn.example.org/uno.mp4", "derechos_confirmados":True,
             "origen":"propio", "credito":"Píxel Feroz",
             "fuente_publica":"https://pixel.example.org/creditos"},
            {"url":"https://cdn.example.org/dos.mp4", "derechos_confirmados":True,
             "origen":"licenciado", "credito":"Autora original",
             "fuente_publica":"https://autora.example.org/licencia"},
        ]
        with patch("video_material.url_segura", side_effect=lambda u: u):
            with patch.dict(os.environ, {"PF_CLIPS_JSON":json.dumps({"gta6":clips})}):
                self.assertEqual(len(catalogo_clips("gta6")), 2)
                self.assertEqual(len(creditos_clips("gta6")), 2)
            clips[1]["derechos_confirmados"] = False
            with patch.dict(os.environ, {"PF_CLIPS_JSON":json.dumps({"gta6":clips})}):
                with self.assertRaisesRegex(ValueError,"derechos"):
                    catalogo_clips("gta6")
            clips[1]["derechos_confirmados"] = True
            clips[1]["origen"] = "sin_autorizacion"
            with patch.dict(os.environ, {"PF_CLIPS_JSON":json.dumps({"gta6":clips})}):
                with self.assertRaisesRegex(ValueError,"Origen"):
                    catalogo_clips("gta6")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Requiere FFmpeg para verificar clips reales")
class TestRenderMixtoFFmpeg(unittest.TestCase):
    def test_short_con_video_y_foto_sin_publicar(self):
        import motor_video

        frases = [
            "Presentamos el material visual disponible y explicamos su relación con Vice City y el mapa anunciado oficialmente por Rockstar.",
            "Este es un segundo fragmento del reportaje para enseñar una imagen real con derechos confirmados y una narración original.",
            "Suscríbete a Píxel Feroz para estar al día de las novedades. Las fuentes verificadas figuran en la descripción.",
        ]
        escenas = [{"tipo": tipo, "texto": texto} for tipo, texto in zip(
            ("gancho", "hecho_verificado", "cierre"), frases
        )]
        guion = " ".join(frases)
        plan = {
            "canal": "Píxel Feroz", "formato": "short",
            "tema_id": "prueba-multimedia",
            "estado": "BORRADOR_PENDIENTE_REVISION",
            "publicacion_automatica": False,
            "titulo_propuesto": "GTA VI: prueba editorial mixta",
            "texto_miniatura": "GTA VI VISUAL",
            "narrador_voz": "Achird",
            "huella_guion": hashlib.sha256(guion.encode()).hexdigest(),
            "escenas": escenas,
        }

        class NarradorSimulado:
            voz = "Achird"
            voz_real = "Audio generado de prueba"
            proveedor = "prueba"
            peticiones = 0
            recuperados = 0

            def __init__(self, formato, plan):
                pass

            def narrar(self, texto, archivo):
                self.peticiones += 1
                with wave.open(str(archivo), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(24000)
                    wav.writeframes(bytes(24000 * 2 * 2))
                return 2.0

        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            foto = base / "test.png"
            Image.new("RGB", (1280, 720), (140, 190, 210)).save(foto)
            video = base / "clip_real.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","color=c=blue:s=640x360:r=20",
                "-t","3.0","-an","-c:v","libx264",
                "-pix_fmt","yuv420p", str(video)
            ], check=True, timeout=45)
            fake_clips = [{"ruta":video,"credito":"Canal", "segundos":3.0}]
            salida = base / "salida"
            with patch.object(motor_video, "SALIDA", salida), patch.object(
                motor_video, "NarradorGemini", NarradorSimulado
            ), patch.object(
                motor_video, "estimar_consumo"
            ), patch.object(
                motor_video, "descargar_clips", return_value=fake_clips
            ), patch.object(
                motor_video, "descargar_imagenes", return_value=[(foto, "Canal")]
            ), patch.dict(os.environ, {"PF_TTS_PROVIDER": "gemini"}):
                motor_video.montar(plan, guion)
            final = salida / "pixel_feroz_short.mp4"
            self.assertTrue(final.exists())
            self.assertGreater(final.stat().st_size, 20000)


if __name__ == "__main__":
    unittest.main()
