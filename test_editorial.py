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
        # La cabecera de la cola cambia cada día: comprobar el orden real
        # y la independencia por formato, sin codificar una fecha pasada.
        # PF-90: el orden real está en las colas, no en el catálogo.
        from cola_editorial_pf import cargar
        cola_shorts = cargar("short")
        cola_largos = cargar("largo")
        primero_short, segundo_short = cola_shorts[:2]
        primero_largo = cola_largos[0]
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "hist.json"
            with patch.object(editorial, "HISTORIAL", hist):
                hist.write_text("[]", encoding="utf-8")
                self.assertEqual(editorial.seleccionado("", "short")["id"], primero_short)
                self.assertEqual(editorial.seleccionado("", "largo")["id"], primero_largo)
                hist.write_text(json.dumps([
                    {"tema_id": primero_short, "estado": "subido", "formato": "short"}
                ]), encoding="utf-8")
                self.assertEqual(editorial.seleccionado("", "short")["id"], segundo_short)
                self.assertEqual(editorial.seleccionado("", "largo")["id"], primero_largo)

    def test_cola_manual_shorts_sabado_21_y_miniaturas(self):
        # Los temas del 21 son históricos: verificar sus portadas sin
        # exigir que sigan siendo los próximos de la cola editorial.
        previstos = [
            ("gta6-mapa-oficial-descargable-20261121", "amarillo", "vice"),
            ("gta6-audio-3d-ps5-20261121", "cian", "artwork"),
            ("gta6-golpe-sin-spoilers-20261121", "fucsia", "duo"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            historial = Path(tmp) / "historial.json"
            historial.write_text("[]", encoding="utf-8")
            with patch.object(editorial, "HISTORIAL", historial):
                for ident, paleta, categoria in previstos:
                    tema = editorial.seleccionado(ident, "short")
                    self.assertEqual(tema["portada_paleta"], paleta)
                    self.assertEqual(tema["portada_categoria"], categoria)
                    self.assertIn("short", tema["formatos"])
                    _, _, plan = editorial.preparar_plan(tema, "short")
                    self.assertEqual(plan["portada_paleta"], paleta)
                    self.assertEqual(plan["portada_categoria"], categoria)
                    self.assertFalse(plan["publicacion_automatica"])

    def test_agenda_domingo_22_solo_privados_y_nuevos_temas(self):
        agenda = json.loads(
            Path(__file__).with_name("calendario_publicacion.json").read_text(encoding="utf-8")
        )
        slots = [s for s in agenda["slots"] if s["fecha"] == "2026-11-22"]
        self.assertEqual(len(slots), 4)
        self.assertEqual([s["formato"] for s in slots], ["short", "short", "short", "largo"])
        self.assertEqual(
            [s["tema_confirmado_reserva"] for s in slots],
            ["gta6-festival-miami-20261122", "gta6-album-disponible-20261122",
             "gta6-bonus-estreno-20261122", "gta6-fin-semana-oficial-20261122"]
        )
        for slot in slots:
            self.assertTrue(slot["subir_siempre_privado"])
            self.assertFalse(slot["publicar_automaticamente"])
            self.assertTrue(slot["requiere_revision_visual"])

    def test_proximo_largo_sabado_21_sobre_radios_no_reserva(self):
        # Comprobación histórica del estilo: el largo del 21 sigue
        # seleccionable por ID si se usa un historial ficticio vacío.
        with tempfile.TemporaryDirectory() as tmp:
            hist = Path(tmp) / "hist.json"
            hist.write_text("[]", encoding="utf-8")
            with patch.object(editorial, "HISTORIAL", hist):
                tema = editorial.seleccionado("gta6-radios-musica-leonida-20261121", "largo")
            self.assertEqual(tema["portada_categoria"], "vice")
            self.assertEqual(tema["portada_paleta"], "violeta")
            _, _, plan = editorial.preparar_plan(tema, "largo")
            self.assertFalse(plan["publicacion_automatica"])
            self.assertTrue(plan["requiere_guion_ia"])

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
