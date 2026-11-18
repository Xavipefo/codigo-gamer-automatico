"""Pruebas sin red para el banco GTA VI y la revisión visual."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import rockstar_media
from revision_visual import anadir_fuente_descripcion, exportar_revision

def zip_de_prueba(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ruta,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for n in range(16):
            color = (n*11 % 255, n*19 % 255, 75)
            imagen = Image.new("RGB",(900,600),color)
            salida=io.BytesIO()
            imagen.save(salida,"JPEG")
            nombre=("Jason Duval" if n<8 else "Vice City")+f" {n+1:02d}.jpg"
            z.writestr("GTAVI/"+nombre,salida.getvalue())

class TestBancoOficial(unittest.TestCase):
    def test_verifica_imagenes_y_selecciona_escenas_distintas(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/"banco"
            with patch.object(rockstar_media,"descargar_zip", side_effect=zip_de_prueba):
                cat=rockstar_media.preparar_banco(base)
            self.assertEqual(len(cat["imagenes"]),16)
            self.assertEqual(cat["origen"],rockstar_media.SOURCE)
            escenas=[{"texto":"Jason Duval aparece en un nuevo avance"} for _ in range(5)]
            plan={"titulo_propuesto":"GTA VI Jason","tema_id":"gta6-jason"}
            fotos=rockstar_media.elegir_imagenes(plan,escenas,base)
            self.assertEqual(len(fotos),5)
            self.assertEqual(len({x[0] for x in fotos}),5)
            self.assertTrue(all(p.is_file() and credito==rockstar_media.CREDITO
                                for p,credito,_ in fotos))
            # Evita los cuatro primeros planos consecutivos del mismo
            # personaje aunque el tema lo mencione en todas las frases.
            etiquetas = [rockstar_media.categoria(t) for _,_,t in fotos]
            self.assertGreaterEqual(etiquetas.count("jason"), 2)
            self.assertTrue(all(
                not (etiquetas[i] == etiquetas[i+1] == etiquetas[i+2])
                for i in range(len(etiquetas)-2)
            ))
            self.assertEqual(len(rockstar_media.cargar_banco(base)["imagenes"]),16)

    def test_zip_malicioso_no_extrae_rutas_externas(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/"banco"
            def malicioso(ruta):
                ruta.parent.mkdir(parents=True,exist_ok=True)
                with zipfile.ZipFile(ruta,"w") as z:
                    z.writestr("../../escape.jpg",b"X"*2000)
            with patch.object(rockstar_media,"descargar_zip",side_effect=malicioso):
                with self.assertRaisesRegex(RuntimeError,"12 capturas"):
                    rockstar_media.preparar_banco(base)
            self.assertFalse((Path(tmp)/"escape.jpg").exists())

    def test_creditos_y_exportacion_para_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            descripcion=base/"descripcion.txt"
            descripcion.write_text("Comentario sobre GTA VI\nFuentes oficiales: https://www.rockstargames.com/VI")
            anadir_fuente_descripcion(descripcion)
            anadir_fuente_descripcion(descripcion)
            s=descripcion.read_text()
            self.assertEqual(s.count("Material visual: capturas oficiales"),1)
            self.assertIn(rockstar_media.SOURCE,s)
            foto=base/"foto.jpg"
            Image.new("RGB",(1280,720),(90,55,130)).save(foto)
            pantalla=base/"frame.png"
            Image.new("RGB",(720,1280),(22,62,95)).save(pantalla)
            exportar_revision(base,[{
                "pantalla":pantalla,"medio":"foto","foto":foto,
                "titulo":"Vice City 01","credito":rockstar_media.CREDITO
            }],catalogo=True)
            out=base/"revision_visual"
            self.assertTrue((out/"mosaico_escenas.jpg").is_file())
            manifest=json.loads((out/"manifiesto_escenas.json").read_text())
            self.assertEqual(len(manifest["escenas"]),1)
            self.assertTrue((out/manifest["escenas"][0]["imagen_usada"]).is_file())

if __name__=="__main__":
    unittest.main()
