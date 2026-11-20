"""PF-41: pruebas sin APIs ni modelo de voz.

Genera fotogramas y voces sintéticas y comprueba el montaje con FFmpeg real.
"""
import json
import math
import shutil
import subprocess
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

from PIL import Image

from ritmo_shorts_rockstar import (
    FPS, contextos_visuales, repartir_fotogramas, preparar_tomas,
    comando_ffmpeg_short, renderizar_short, compactar_pausas_wav,
)
from preparar_contenido import preparar, CTA_SUSCRIPCION


class TestPlanPF41(unittest.TestCase):
    def test_cortes_3_8_s_sin_perder_frames(self):
        for n in (1, 30, 76, 77, 105, 180, 420):
            trozos = repartir_fotogramas(n)
            self.assertEqual(sum(trozos), n)
            self.assertTrue(all(0 < x <= 76 for x in trozos))
        self.assertEqual(repartir_fotogramas(120), [60, 60])

    def test_fotografias_contextuales_por_bloque(self):
        escenas = [{"tipo": "gancho", "texto": (
            "Rockstar muestra a Lucia recorriendo las calles de Vice City "
            "y la presentación del mundo de Leonida en GTA VI."
        )}]
        visuales = contextos_visuales(escenas)
        self.assertEqual(len(visuales), 6)
        self.assertTrue(all("Vice City" in x["texto"] for x in visuales))
        self.assertTrue(all(x["tipo"] == "gancho" for x in visuales))

    def test_cierre_corto_y_datos_con_fuente(self):
        tema = {
            "id": "gta6-test-pf41", "titulo": "GTA VI: novedades verificadas",
            "gancho": "Rockstar ha mostrado nuevos detalles sobre GTA VI.",
            "contexto": "La información procede de su sitio oficial.",
            "hechos": [
                {"texto": "Vice City forma parte de Leonida.",
                 "fuente": "https://www.rockstargames.com/VI"},
                {"texto": "Jason y Lucia protagonizan el juego.",
                 "fuente": "https://www.rockstargames.com/VI"},
                {"texto": "Rockstar muestra diferentes escenarios oficiales.",
                 "fuente": "https://www.rockstargames.com/VI"},
            ],
        }
        # Evitar descargar material en construir_descripcion.
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            descripcion = Path(tmp) / "general.txt"
            descripcion.write_text("Canal de videojuegos", encoding="utf-8")
            with patch("preparar_contenido.DESCRIPCION_COMUN", descripcion), patch(
                "visuales_autorizados.creditos_para_descripcion", return_value=[]
            ), patch("video_material.creditos_clips", return_value=[]):
                guion, _, plan = preparar(tema)
        self.assertEqual(plan["escenas"][-1]["texto"], CTA_SUSCRIPCION)
        self.assertEqual(plan["duracion_objetivo_segundos"], [25, 42])
        self.assertEqual(guion, " ".join(x["texto"] for x in plan["escenas"]))
        self.assertLessEqual(len(guion.split()), 88)
        self.assertTrue(all(
            s.get("fuente") for s in plan["escenas"] if s["tipo"] == "hecho_verificado"
        ))

    def test_compacta_silencio_largo_conservando_voz(self):
        frecuencia = 12000
        def tono(segundos):
            return array("h", (
                int(6500 * math.sin(2*math.pi*220*i/frecuencia))
                for i in range(int(segundos*frecuencia))
            ))
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "audio.wav"
            original = array("h")
            original.extend(tono(1.5))
            original.extend([0]*frecuencia)
            original.extend(tono(1.5))
            with wave.open(str(archivo), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(frecuencia)
                wav.writeframes(original.tobytes())
            resultado = compactar_pausas_wav(archivo)
            self.assertGreater(resultado, 3.0)
            self.assertLess(resultado, 3.7)
            with wave.open(str(archivo), "rb") as wav:
                self.assertEqual(wav.getframerate(), frecuencia)
                self.assertEqual(wav.getnchannels(), 1)

    def test_silencio_puro_no_recorta_audio_de_pruebas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            archivo = Path(carpeta) / "silencio.wav"
            with wave.open(str(archivo), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(24000)
                wav.writeframes(bytes(24000*2*2))
            self.assertAlmostEqual(compactar_pausas_wav(archivo), 2.0, places=2)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg necesario")
class TestRenderPF41(unittest.TestCase):
    def test_tres_planos_y_voz_unica_en_short(self):
        with tempfile.TemporaryDirectory() as carpeta:
            carpeta = Path(carpeta)
            fotos = []
            for i in range(3):
                foto = carpeta / f"foto_{i}.jpg"
                Image.new("RGB", (1280, 720),
                          (40+i*60, 80+i*30, 160)).save(foto)
                fotos.append((foto, "Rockstar Games", "Leonida oficial"))
            audio = carpeta / "narracion.wav"
            with wave.open(str(audio), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(12000)
                wav.writeframes(bytes(12000*2*6))
            tomas = preparar_tomas(
                fotos,
                {"tipo": "gancho", "texto":
                 "GTA VI muestra nuevas regiones oficiales con personajes "
                 "y escenarios distintos de Leonida."},
                120, carpeta, 0,
            )
            self.assertEqual(len(tomas), 2)
            self.assertTrue(all(t["archivo"].is_file() for t in tomas))
            orden = comando_ffmpeg_short(tomas, audio, carpeta / "salida.mp4")
            self.assertEqual(orden.count("-i"), 3)
            salida = carpeta / "salida.mp4"
            renderizar_short(
                tomas, audio, salida,
                lambda args: subprocess.run(args, check=True, timeout=180)
            )
            self.assertGreater(salida.stat().st_size, 5000)
            p = subprocess.run([
                "ffprobe", "-v", "error", "-show_format", "-show_streams",
                "-of", "json", str(salida)
            ], check=True, capture_output=True, text=True, timeout=15)
            info = json.loads(p.stdout)
            streams = info["streams"]
            v = next(x for x in streams if x["codec_type"]=="video")
            a = next(x for x in streams if x["codec_type"]=="audio")
            self.assertEqual((v["width"], v["height"]), (720, 1280))
            self.assertEqual(a["codec_name"], "aac")
            self.assertAlmostEqual(float(info["format"]["duration"]), 6.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
