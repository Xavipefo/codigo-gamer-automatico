"""El calendario y la preproducción de GTA VI nunca suben vídeos."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from planificar_lanzamiento import CALENDARIO, TEMAS, IDEAS, comprobar_calendario, preparar


class TestPlanLanzamiento(unittest.TestCase):
    def test_dias_horario_y_solo_privado(self):
        cal = json.loads(CALENDARIO.read_text(encoding="utf-8"))
        temas = {x["id"]: x for x in json.loads(TEMAS.read_text(encoding="utf-8"))}
        ideas = {x["id"]: x for x in json.loads(IDEAS.read_text(encoding="utf-8"))["ideas"]}
        self.assertTrue(comprobar_calendario(cal, temas, ideas))
        self.assertEqual(len(cal["slots"]), 25)
        self.assertTrue(all(x["subir_siempre_privado"] for x in cal["slots"]))
        self.assertFalse(any(x["publicar_automaticamente"] for x in cal["slots"]))
        especiales = [x for x in cal["slots"] if x["fecha"] >= "2026-11-19"]
        self.assertEqual(sum(x["formato"] == "short" for x in especiales), 16)
        self.assertEqual(sum(x["formato"] == "largo" for x in especiales), 6)

    def test_19_noviembre_dos_extras_y_ocho_videos_diurnos(self):
        cal = json.loads(CALENDARIO.read_text(encoding="utf-8"))
        dia = sorted((s for s in cal["slots"] if s["fecha"] == "2026-11-19"),
                     key=lambda x: x["hora"])
        self.assertEqual(len(dia), 10)
        self.assertEqual([s["hora"] for s in dia[:2]], ["00:05", "00:20"])
        self.assertEqual([s["formato"] for s in dia[:2]], ["short", "largo"])
        diurnos = dia[2:]
        self.assertEqual(sum(s["formato"] == "short" for s in diurnos), 6)
        self.assertEqual(sum(s["formato"] == "largo" for s in diurnos), 2)
        self.assertTrue(all(s["subir_siempre_privado"] for s in dia))
        self.assertFalse(any(s["publicar_automaticamente"] for s in dia))
        self.assertEqual(len({s["tema_confirmado_reserva"] for s in dia}), 10)

    def test_rechazar_activar_publicacion(self):
        cal = json.loads(CALENDARIO.read_text(encoding="utf-8"))
        temas = {x["id"]: x for x in json.loads(TEMAS.read_text(encoding="utf-8"))}
        ideas = {x["id"]: x for x in json.loads(IDEAS.read_text(encoding="utf-8"))["ideas"]}
        cal["slots"][0]["publicar_automaticamente"] = True
        with self.assertRaisesRegex(ValueError, "Prohibido"):
            comprobar_calendario(cal, temas, ideas)

    def test_borradores_y_portadas_no_generan_publicaciones(self):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "pack"
            resultado = preparar(destino=destino)
            self.assertEqual(len(resultado), 25)
            self.assertTrue((destino / "agenda.md").is_file())
            self.assertTrue((destino / "pendientes_verificacion.json").is_file())
            self.assertTrue(any((destino / "borradores").glob("*/opciones_ab/miniatura_a.jpg")))
            self.assertFalse(any(destino.rglob("*.mp4")))
            self.assertFalse(any(destino.rglob("*.wav")))


if __name__ == "__main__":
    unittest.main()
