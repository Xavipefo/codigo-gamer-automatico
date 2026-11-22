"""QC-01: pruebas con MP4 sintéticos reales, sin redes ni YouTube."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from auditoria_audiovisual import auditar

FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


@unittest.skipUnless(FFMPEG, "FFmpeg no está instalado")
class AuditoriaReal(unittest.TestCase):
    def setUp(self):
        self.carpeta=tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)
        self.dest=Path(self.carpeta.name)

    def crear(self, nombre, filtro="testsrc2=size=320x568:rate=12", audio=True):
        salida=self.dest/nombre
        cmd=["ffmpeg","-y","-hide_banner","-loglevel","error",
             "-f","lavfi","-i",filtro]
        if audio:
            cmd+=["-f","lavfi","-i","sine=frequency=440:sample_rate=16000",
                  "-shortest"]
        cmd+=["-t","4","-c:v","libx264","-preset","ultrafast",
              "-pix_fmt","yuv420p"]
        if audio:
            cmd+=["-c:a","aac","-b:a","96k"]
        cmd+=[str(salida)]
        subprocess.run(cmd,check=True,capture_output=True,timeout=45)
        return salida

    def test_video_con_imagenes_moviles_y_narracion_aprobado(self):
        ruta=self.crear("movimiento.mp4")
        reporte=auditar(ruta,"vertical",minimo=3,maximo=9)
        self.assertEqual(reporte["estado"],"apto_tecnicamente_para_revision_privada")
        self.assertTrue(reporte["pendiente_revision_editorial"])
        self.assertEqual(reporte["orientacion"],"vertical")

    def test_bloquea_video_sin_audio(self):
        ruta=self.crear("sin_audio.mp4",audio=False)
        with self.assertRaisesRegex(ValueError,"narración"):
            auditar(ruta,"vertical",minimo=3,maximo=9)

    def test_bloquea_cuadro_congelado(self):
        ruta=self.crear("fijo.mp4","color=c=red:s=320x568:r=12")
        with self.assertRaisesRegex(ValueError,"congelado"):
            auditar(ruta,"vertical",minimo=3,maximo=9)

    def test_bloquea_orientacion_incorrecta(self):
        ruta=self.crear("vertical.mp4")
        with self.assertRaisesRegex(ValueError,"horizontal"):
            auditar(ruta,"horizontal",minimo=3,maximo=9)


if __name__=="__main__":
    unittest.main()
