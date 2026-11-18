"""Contrato de lanzamiento de GTA VI: cola, visuales y publicación segura.

Estas pruebas no acceden a redes, ni generan MP4, ni publican en YouTube.
"""
import json
import unittest
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent

class TestEstreno19Noviembre(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temas = {t["id"]:t for t in json.loads(
            (BASE/"temas_verificados.json").read_text(encoding="utf-8"))}
        cls.slots = json.loads(
            (BASE/"calendario_publicacion.json").read_text(encoding="utf-8"))["slots"]

    def test_seis_tematicas_confirmadas_y_ordenadas(self):
        previstos = [
            ("gta6-estreno-espana-0005", "short", "00:05"),
            ("gta6-estreno-tres-claves", "short", "09:00"),
            ("gta6-estreno-jason-lucia", "short", "12:30"),
            ("gta6-estreno-zonas-leonida", "short", "16:30"),
            ("gta6-estreno-ediciones", "short", "20:00"),
            ("gta6-estreno-resumen-oficial-largo", "largo", "22:00"),
        ]
        for ident, formato, hora in previstos:
            with self.subTest(tema=ident):
                tema=self.temas[ident]
                self.assertEqual(tema["estado"],"confirmado")
                self.assertIn(formato,tema["formatos"])
                objetivo=datetime.fromisoformat(tema["publicacion_objetivo"])
                self.assertEqual(objetivo.strftime("%Y-%m-%d %H:%M"),"2026-11-19 "+hora)
                self.assertEqual(objetivo.utcoffset().total_seconds(),3600)
                self.assertGreaterEqual(len(tema["hechos"]),3)
                self.assertTrue(all(h["fuente"].startswith("https://") for h in tema["hechos"]))
                self.assertGreaterEqual(len(tema.get("visuales_preferidos",[])),3)
                relacionados=[slot for slot in self.slots if slot.get("tema_confirmado_reserva")==ident]
                self.assertEqual(len(relacionados),1)
                self.assertEqual(relacionados[0]["hora"],hora)
                self.assertFalse(relacionados[0]["publicar_automaticamente"])
                self.assertTrue(relacionados[0]["subir_siempre_privado"])

    def test_medianoche_no_puede_presentarse_como_publicacion_programada(self):
        t=self.temas["gta6-estreno-espana-0005"]
        self.assertEqual(t["publicacion_manual_desde"],"2026-11-19T00:05:00+01:00")
        calendario=json.loads((BASE/"calendario_publicacion.json").read_text(encoding="utf-8"))
        self.assertIn("MANUAL",calendario["nota"].upper())

    def test_largos_disponen_de_material_multimedia_real(self):
        codigo=(BASE/"motor_video.py").read_text(encoding="utf-8")
        flujo=(BASE/".github/workflows/produccion_completa.yml").read_text(encoding="utf-8")
        self.assertIn('formato == "largo"',codigo)
        self.assertIn("elegir_tomas(",codigo)
        self.assertIn("renderizar(tomas,",codigo)
        self.assertIn("rockstar_clips.py --preparar",flujo)
        self.assertIn("rockstar_extras.py --preparar",flujo)
        self.assertIn("salida/revision_visual/",flujo)
        self.assertIn("run: python subir_youtube_privado.py",flujo)

if __name__=="__main__":
    unittest.main()
