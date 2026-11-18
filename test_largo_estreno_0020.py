"""Largo especial de lanzamiento: guion cerrado y comparación limitada."""
import json
import unittest
from datetime import datetime
from pathlib import Path
from editorial import preparar_plan
from preparar_contenido import validar_tema

BASE=Path(__file__).resolve().parent
ID="gta6-ya-se-puede-jugar-0020-largo"

class TestLargoEstreno0020(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tema=next(t for t in json.loads((BASE/"temas_verificados.json").read_text(encoding="utf-8")) if t["id"]==ID)

    def test_largo_de_estreno_no_es_una_comparativa_completa(self):
        t=validar_tema(self.tema)
        escenas=t["escenas_largas"]
        self.assertEqual(len(escenas),14)
        self.assertTrue(1100 <= len(" ".join(escenas).split()) <= 1800)
        comparativa=escenas[9].split()
        self.assertTrue(145 <= len(comparativa) <= 205)
        self.assertIn("GTA cinco",escenas[9])
        self.assertTrue(all(len(s.split())>=20 for s in escenas))
        plan_texto,descripcion,plan=preparar_plan(t,"largo")
        self.assertFalse(plan["requiere_guion_ia"])
        self.assertEqual(plan["tema_id"],ID)
        self.assertEqual(len(plan["escenas"]),14)
        self.assertIn("GTA cinco",plan_texto)
        self.assertTrue("https://www.rockstargames.com/VI" in descripcion)
        self.assertIs(plan["publicacion_automatica"],False)

    def test_hora_manual_y_no_publicacion_automatica(self):
        objetivo=datetime.fromisoformat(self.tema["publicacion_objetivo"])
        self.assertEqual(objetivo.strftime("%Y-%m-%d %H:%M"),"2026-11-19 00:20")
        self.assertEqual(objetivo.utcoffset().total_seconds(),3600)
        calendario=json.loads((BASE/"calendario_publicacion.json").read_text(encoding="utf-8"))
        slots=[s for s in calendario["slots"] if s.get("tema_confirmado_reserva")==ID]
        self.assertEqual(len(slots),1)
        self.assertEqual(slots[0]["hora"],"00:20")
        self.assertTrue(slots[0]["subir_siempre_privado"])
        self.assertFalse(slots[0]["publicar_automaticamente"])

if __name__=="__main__":
    unittest.main()
