"""Validación determinista del motor editorial (sin red, sin render, sin subir)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import editorial


class TestEditorial(unittest.TestCase):
    def test_candidatos_y_planes(self):
        temas=editorial.cargar_elegibles()
        self.assertTrue(temas)
        t=temas[0]
        guion,desc,plan=editorial.preparar_plan(t,"short")
        self.assertEqual(
            " ".join(s["texto"].strip() for s in plan["escenas"]),
            guion
        )
        self.assertEqual(plan["publicacion_automatica"],False)
        self.assertTrue(plan["revision_pendiente"])
        self.assertIn("https://",desc)

    def test_descartar_historico(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist=Path(tmp)/"hist.json"
            hist.write_text(json.dumps([
                {"tema_id":"gta6-jason-lucia","estado":"subido"}
            ]),encoding="utf-8")
            with patch.object(editorial,"HISTORIAL",hist):
                with self.assertRaises(ValueError):
                    editorial.seleccionado("gta6-jason-lucia","short")

    def test_largo_sin_guion_no_inventa(self):
        with self.assertRaises(ValueError):
            editorial.seleccionado("gta6-jason-lucia","largo")


if __name__=="__main__":
    unittest.main()
