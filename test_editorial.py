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

    def test_largo_requiere_guion_ia(self):
        # La prueba no debe depender del historial real de vídeos ya subidos.
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "hist.json"
            hist.write_text("[]", encoding="utf-8")
            with patch.object(editorial, "HISTORIAL", hist):
                tema = editorial.seleccionado("gta6-jason-lucia", "largo")
        guion, descripcion, plan = editorial.preparar_plan(tema, "largo")
        self.assertEqual(guion, "")
        self.assertTrue(plan["requiere_guion_ia"])
        self.assertEqual(plan["formato"], "largo")
        self.assertNotIn("Formato editorial:", descripcion)
        self.assertNotIn("Identificador editorial:", descripcion)

    def test_orden_y_formatos_independientes(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "hist.json"
            hist.write_text(json.dumps([
                {"tema_id": "gta6-lanzamiento-oficial",
                 "estado": "subido", "formato": "short"}
            ]), encoding="utf-8")
            with patch.object(editorial, "HISTORIAL", hist):
                proximo = editorial.seleccionado("", "short")
                self.assertEqual(proximo["id"], "gta6-estreno-espana-0005")
                largo = editorial.seleccionado("", "largo")
                self.assertEqual(largo["id"], "gta6-estreno-resumen-oficial-largo")

    def test_descripcion_general_y_suscripcion(self):
        tema = editorial.cargar_elegibles()[0]
        guion, descripcion, plan = editorial.preparar_plan(tema, "short")
        self.assertIn("Suscríbete a Píxel Feroz", guion)
        self.assertIn("Bienvenido a PÍXEL FEROZ", descripcion)
        self.assertIn("FUENTES OFICIALES:", descripcion)
        self.assertNotIn("Formato editorial:", descripcion)
        self.assertNotIn("Identificador editorial:", descripcion)
        self.assertNotIn("PF-ID:", descripcion)
        self.assertTrue(plan["texto_miniatura"])


if __name__=="__main__":
    unittest.main()
