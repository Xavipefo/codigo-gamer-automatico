"""PF-43: cola editorial nueva contrastada con fuentes oficiales de Rockstar."""
import unittest
from pathlib import Path
import json
from unittest.mock import patch

from preparar_contenido import validar_tema
import editorial

RAIZ=Path(__file__).resolve().parent
IDS=(
    "gta6-vice-city-fotos-oficiales",
    "gta6-leonida-keys-fotos",
    "gta6-grassrivers-oficial",
    "gta6-port-gellhorn-galeria",
    "gta6-ambrosia-imagenes",
    "gta6-mount-kalaga-parque",
    "gta6-real-dimez-bae-roxy",
    "gta6-only-raw-records",
    "gta6-galeria-videos-oficiales",
    "gta6-escenas-leonida-sin-spoilers",
    "gta6-vice-city-escena-musical",
)


class ColaPF43(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        datos=json.loads((RAIZ/"temas_verificados.json").read_text(encoding="utf-8"))
        cls.datos=datos
        cls.nuevos={x["id"]:x for x in datos if x["id"] in IDS}

    def test_contiene_nueve_shorts_y_dos_largos_sin_duplicados(self):
        self.assertEqual(len(self.nuevos),11)
        self.assertEqual(len({x["id"] for x in self.datos}),len(self.datos))
        self.assertEqual(sum("short" in x["formatos"] for x in self.nuevos.values()),9)
        self.assertEqual(sum("largo" in x["formatos"] for x in self.nuevos.values()),2)

    def test_solo_hechos_oficiales_y_largos_con_esquema(self):
        for id,tema in self.nuevos.items():
            with self.subTest(id=id):
                self.assertIs(validar_tema(tema),tema)
                self.assertTrue(all(
                    x["fuente"].startswith("https://www.rockstargames.com/")
                    for x in tema["hechos"]
                ))
                self.assertTrue(tema["visuales_preferidos"])
                if "largo" in tema["formatos"]:
                    self.assertGreaterEqual(len(tema["esquema_largo"]),8)
                    self.assertEqual(len(tema["miniatura_opciones"]),3)
                    self.assertEqual(len(tema["titulos_experimento"]),3)

    def test_prioriza_nuevos_temas_no_publicados(self):
        hist=RAIZ/"historial_publicados.json"
        with patch.object(editorial,"HISTORIAL",hist):
            next_short=editorial.seleccionado("","short")
            next_long=editorial.seleccionado("","largo")
        self.assertEqual(next_short["id"],IDS[0])
        self.assertEqual(next_long["id"],IDS[-2])

    def test_plan_y_descripcion_primer_short(self):
        tema=self.nuevos[IDS[0]]
        texto,desc,plan=editorial.preparar_plan(tema,"short")
        self.assertGreater(len(texto.split()),40)
        self.assertFalse(plan["publicacion_automatica"])
        self.assertIn("rockstargames.com",desc)


if __name__=="__main__":
    unittest.main()
