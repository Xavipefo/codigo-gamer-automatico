"""PF-90: control de la cola oficial y las ideas pendientes de verificar."""
import json
import tempfile
import unittest
from pathlib import Path
from cola_editorial_pf import cargar, ordenar, retirar

BASE = Path(__file__).resolve().parent

class ColasPF90(unittest.TestCase):
    def test_shorts_largos_ordenados_independientemente(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t)
            (base/"colas").mkdir()
            (base/"colas"/"shorts.json").write_text('["s2", "s1"]',encoding="utf-8")
            (base/"colas"/"documentales.json").write_text('["l1"]',encoding="utf-8")
            self.assertEqual([x["id"] for x in ordenar([{"id":"s1"},{"id":"s2"}],"short",base)],["s2","s1"])
            self.assertTrue(retirar("short","s2",base))
            self.assertEqual(cargar("short",base),["s1"])
            self.assertEqual(cargar("largo",base),["l1"])
            self.assertFalse(retirar("short","s2",base))
            (base/"colas"/"shorts.json").write_text("[]",encoding="utf-8")
            self.assertEqual(ordenar([{"id":"s1"}],"short",base),[])

    def test_todos_confirmados_tienen_fuentes_y_vigencia(self):
        from datetime import date
        from preparar_contenido import comprobar_enlace
        hoy=date.today()
        catalogo={x["id"]:x for x in json.loads((BASE/"temas_verificados.json").read_text(encoding="utf-8"))}
        for formato in ("short","largo"):
            for tema_id in cargar(formato):
                self.assertIn(tema_id,catalogo)
                t=catalogo[tema_id]
                self.assertEqual(t["estado"],"confirmado")
                self.assertIn(formato,t["formatos"])
                self.assertTrue(all(comprobar_enlace(h["fuente"]) for h in t["hechos"]))
                if t.get("vigente_hasta"):
                    self.assertGreaterEqual(date.fromisoformat(t["vigente_hasta"]),hoy)

    def test_tres_meses_de_ideas_no_se_inventan_hechos(self):
        cal=json.loads((BASE/"colas"/"calendario_3meses.json").read_text(encoding="utf-8"))
        short=json.loads((BASE/"colas"/"ideas_shorts_3meses.json").read_text(encoding="utf-8"))
        largo=json.loads((BASE/"colas"/"ideas_documentales_3meses.json").read_text(encoding="utf-8"))
        self.assertEqual(cal["inicio"],"2026-11-24")
        self.assertEqual(cal["fin"],"2027-02-23")
        self.assertGreaterEqual(len(short)+len(cargar("short")),cal["cuota"]["shorts"])
        self.assertGreaterEqual(len(largo)+len(cargar("largo")),cal["cuota"]["largos"])
        self.assertTrue(all(x["estado"]=="pendiente_verificacion" for x in short+largo))
        self.assertTrue(all(x["publicacion_automatica"] is False for x in short+largo))
        self.assertTrue(all(x["estado"] in ("tema_confirmado","idea_pendiente_verificacion") for x in cal["slots"]))

if __name__=="__main__":
    unittest.main()
