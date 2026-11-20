"""PF-41: el motor COMPLETO produce imágenes oficiales desde el primer plano.

Prueba local sin IA, sin red y sin YouTube; usa narración simulada y fotos de
prueba; no afirma que estas fotos sintéticas sean material de Rockstar.
"""
import json
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import motor_video


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg necesario para render real")
class IntegracionShortPF41(unittest.TestCase):
    def test_short_real_usa_planos_en_motor_y_entrega_informe(self):
        frases = [
            "Rockstar muestra las ciudades y los personajes de GTA VI en"
            " material oficial de la nueva región de Leonida.",
            "La presentación incluye escenarios diversos de Vice City"
            " y nuevos protagonistas que aparecen en las capturas anunciadas.",
            "Suscríbete a Píxel Feroz.",
        ]
        escenas = [
            {"tipo": tipo, "texto": texto} for tipo, texto in zip(
                ("gancho", "hecho_verificado", "cierre"), frases
            )
        ]
        guion = " ".join(frases)
        plan = {
            "canal": "Píxel Feroz", "formato": "short",
            "tema_id": "gta6-prueba-fotografias-pf41",
            "estado": "BORRADOR_PENDIENTE_REVISION",
            "publicacion_automatica": False,
            "titulo_propuesto": "GTA VI - personajes y ciudades",
            "texto_miniatura": "GTA VI: LEONIDA",
            "escenas": escenas,
        }
        numero_bloques = len(motor_video.adaptar_escenas(plan))
        llamadas = []

        class NarradorPrueba:
            proveedor = "prueba"
            voz = "Ryan"
            voz_real = "WAV de prueba"
            recuperados = 0

            def __init__(self, formato, plan):
                self.peticiones = 0

            def narrar(self, texto, destino):
                llamadas.append(texto)
                self.peticiones += 1
                with wave.open(str(destino), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(24000)
                    wav.writeframes(bytes(24000 * 2 * 5))
                return 5.0

        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            fotos = []
            for i in range(6):
                imagen = raiz / f"foto_{i}.jpg"
                Image.new("RGB", (1280, 720),
                          (20+i*24, 70+i*19, 130)).save(imagen)
                fotos.append(imagen)
            out = raiz / "salida"
            autorizadas = [
                (fotos[i % len(fotos)], "Rockstar Games - prueba sintética",
                 f"Toma ficticia de prueba {i}")
                for i in range(numero_bloques * 6)
            ]
            def miniatura(_texto, _formato, destino, plan=None):
                Image.new("RGB", (720, 1280), (10, 30, 45)).save(
                    destino, format="JPEG"
                )
            with (
                patch.object(motor_video, "SALIDA", out),
                patch.object(motor_video, "NarradorGemini", NarradorPrueba),
                patch.object(motor_video, "estimar_consumo"),
                patch.object(motor_video, "descargar_clips", return_value=[]),
                patch.object(motor_video, "descargar_imagenes", return_value=[]),
                patch.object(motor_video, "elegir_imagenes", return_value=autorizadas),
                patch.object(motor_video, "crear_miniatura", side_effect=miniatura),
                patch.object(motor_video, "exportar_revision"),
                patch.object(motor_video, "anadir_fuente_descripcion"),
                patch.dict(os.environ, {
                    "PF_ROCKSTAR_MEDIA": "1",
                    "PF_TTS_PROVIDER": "gemini",
                }),
            ):
                motor_video.montar(plan, guion)
            video = out / "pixel_feroz_short.mp4"
            reporte = out / "informe_ritmo_pf41.json"
            self.assertTrue(video.is_file())
            self.assertTrue(reporte.is_file())
            self.assertEqual(len(llamadas), numero_bloques)
            datos = json.loads(reporte.read_text(encoding="utf-8"))
            self.assertEqual(datos["primer_plano"], "foto")
            self.assertGreaterEqual(datos["numero_planos"], 4)
            self.assertLessEqual(datos["plano_maximo_segundos"], 3.8)
            self.assertAlmostEqual(datos["duracion_segundos"], numero_bloques*5.25, delta=0.4)
            self.assertTrue(all(x["medio"] == "foto" for x in datos["planos"]))


if __name__ == "__main__":
    unittest.main()
