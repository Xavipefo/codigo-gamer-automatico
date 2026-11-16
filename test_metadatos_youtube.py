"""Test de etiquetas internas y protección de vídeos duplicados, sin red."""
import unittest
from unittest.mock import MagicMock

from metadatos_youtube import (
    normalizar_etiquetas, etiquetas_internas,
    es_duplicado, limpiar_marcadores_anteriores,
)
from preparar_contenido import construir_descripcion
from editorial import cargar_elegibles


class TestMetadatosYouTube(unittest.TestCase):
    def test_descripcion_sin_codigos_editoriales(self):
        tema = cargar_elegibles()[0]
        for formato in ("short", "largo"):
            d = construir_descripcion(tema, formato)
            self.assertNotIn("Identificador editorial:", d)
            self.assertNotIn("Formato editorial:", d)
            self.assertNotIn("PF-ID:", d)
            self.assertNotIn("PF-FORMATO:", d)
            self.assertIn("FUENTES OFICIALES:", d)
            self.assertIn(tema["titulo"], d)
            self.assertIn("Bienvenido a PÍXEL FEROZ", d)

    def test_tags_almacenan_id_y_formato_sin_publicar_en_descripcion(self):
        self.assertEqual(
            etiquetas_internas("gta6-jason-lucia", "short"),
            ["pf_id_gta6-jason-lucia", "pf_formato_short"],
        )
        tags = normalizar_etiquetas(
            ["GTA VI", "videojuegos", "GTA VI"],
            "gta6-jason-lucia", "short"
        )
        self.assertEqual(tags, [
            "GTA VI", "videojuegos",
            "pf_id_gta6-jason-lucia", "pf_formato_short"
        ])

    def test_no_duplica_mismo_formato_con_tags(self):
        snippet = {"tags": [
            "videojuegos", "pf_id_gta6-jason-lucia", "pf_formato_short"
        ], "description": "Noticia de videojuegos. Fuentes oficiales."}
        self.assertTrue(es_duplicado(snippet, "gta6-jason-lucia", "short"))
        self.assertFalse(es_duplicado(snippet, "gta6-jason-lucia", "largo"))
        self.assertFalse(es_duplicado(snippet, "otra-noticia", "short"))

    def test_conserva_detectabilidad_antigua_descripcion(self):
        snippet = {"tags": [], "description": (
            "Antiguo vídeo\n"
            "Identificador editorial: PF-ID:gta6-jason-lucia\n"
            "Formato editorial: PF-FORMATO:short\n"
        )}
        self.assertTrue(es_duplicado(snippet, "gta6-jason-lucia", "short"))
        self.assertFalse(es_duplicado(snippet, "gta6-jason-lucia", "largo"))

    def test_legacy_sin_formato_se_trata_como_short(self):
        snippet = {"tags": [], "description":
                   "Identificador editorial: PF-ID:gta6-jason-lucia"}
        self.assertTrue(es_duplicado(snippet, "gta6-jason-lucia", "short"))
        self.assertFalse(es_duplicado(snippet, "gta6-jason-lucia", "largo"))

    def test_etiqueta_incompleta_bloquea_por_seguridad(self):
        snippet = {"tags": ["pf_id_gta6-jason-lucia"]}
        self.assertTrue(es_duplicado(snippet, "gta6-jason-lucia", "largo"))
        self.assertTrue(es_duplicado(snippet, "gta6-jason-lucia", "short"))

    def test_limpieza_anteriores_mantiene_fuentes_y_otra_descripcion(self):
        antiguo = (
            "El vídeo trata sobre GTA.\n"
            "FUENTES OFICIALES:\nhttps://www.rockstargames.com/VI\n"
            "Identificador editorial: PF-ID:gta6-jason-lucia\n"
            "Formato editorial: PF-FORMATO:short\n"
        )
        nuevo = limpiar_marcadores_anteriores(antiguo)
        self.assertIn("El vídeo trata sobre GTA", nuevo)
        self.assertIn("FUENTES OFICIALES", nuevo)
        self.assertNotIn("editorial", nuevo.lower())


if __name__ == "__main__":
    unittest.main()
