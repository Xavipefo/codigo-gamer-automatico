"""Pruebas de subplanos largos con fotos y clips locales, sin red."""
import json
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image
from montaje_rockstar import repartir_frames,elegir_tomas,rotulo_editorial,crear_preview,renderizar

class TestPlanVisual(unittest.TestCase):
    def test_plano_cada_siete_segundos(self):
        piezas=repartir_frames(20*31+5)
        self.assertEqual(sum(piezas),625)
        self.assertTrue(all(0<x<=140 for x in piezas))
        self.assertGreaterEqual(len(piezas),5)

    def test_fotos_con_clip_en_intervalos(self):
        fotos=[(Path("/tmp/foto.jpg"),"Rockstar Games","Vice City")]*2
        clips=[{"ruta":Path("/tmp/video.mp4"),"credito":"Rockstar Games","nombre":"Jason"}]
        tomas=elegir_tomas(fotos,clips,20*19,0)
        self.assertTrue(any(t["tipo"]=="clip" for t in tomas))
        self.assertEqual(sum(t["frames"] for t in tomas),380)

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg necesario")
class TestFFmpegMultimedia(unittest.TestCase):
    def test_mezcla_clip_y_fotos_con_una_narracion(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            fotos=[]
            for i in (1,2):
                foto=p/f"foto_{i}.jpg"
                Image.new("RGB",(1280,720),(30*i,110,150)).save(foto)
                fotos.append((foto,"Rockstar Games",f"Vice City {i}"))
            clip=p/"clip.mp4"
            subprocess.run([
                "ffmpeg","-hide_banner","-loglevel","error","-y",
                "-f","lavfi","-i","color=c=red:s=640x360:r=20",
                "-t","3","-an","-c:v","libx264","-pix_fmt","yuv420p",str(clip)
            ],check=True,timeout=45)
            wav=p/"voz.wav"
            with wave.open(str(wav),"wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
                w.writeframes(bytes(24000*2*10))
            capa=rotulo_editorial(
                {"texto":"El lanzamiento de GTA VI tiene imágenes verificadas de Rockstar Games."},
                p/"capa.png"
            )
            tomas=[
                {"tipo":"foto","ruta":fotos[0][0],"frames":80,"credito":"Rockstar Games","titulo":"Vice City"},
                {"tipo":"clip","ruta":clip,"frames":60,"credito":"Rockstar Games","titulo":"Jason"},
                {"tipo":"foto","ruta":fotos[1][0],"frames":60,"credito":"Rockstar Games","titulo":"Lucia"},
            ]
            previo=crear_preview(tomas[1],capa,p/"preview.jpg")
            self.assertTrue(previo.is_file())
            salida=p/"largo.mp4"
            renderizar(tomas,capa,wav,salida,lambda args: subprocess.run(args,check=True,timeout=180))
            r=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams",
                              "-of","json",str(salida)],check=True,capture_output=True,text=True,timeout=15)
            info=json.loads(r.stdout)
            self.assertGreater(salida.stat().st_size,10000)
            self.assertAlmostEqual(float(info["format"]["duration"]),10.0,delta=0.7)

if __name__=="__main__":
    unittest.main()
