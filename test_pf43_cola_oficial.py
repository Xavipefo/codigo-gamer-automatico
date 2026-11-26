"""PF-43: cola editorial nueva contrastada con fuentes oficiales de Rockstar."""
import unittest
from pathlib import Path
import json
import tempfile
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
        # Un historial de producción real es mutable; el test no debe depender
        # de las subidas que se hayan hecho en el canal.
        with tempfile.TemporaryDirectory() as tmp:
            hist=Path(tmp)/"historial.json"
            hist.write_text("[]", encoding="utf-8")
            with patch.object(editorial,"HISTORIAL",hist):
                next_short=editorial.seleccionado("","short")
                from cola_editorial_pf import cargar
                cola_short = cargar("short")
                cola_largo = cargar("largo")
                self.assertGreaterEqual(len(cola_short), 2)
                self.assertEqual(next_short["id"],cola_short[0])
                if cola_largo:
                    self.assertEqual(editorial.seleccionado("","largo")["id"],cola_largo[0])
                else:
                    # Es correcto agotar la cola de documentales: no crear
                    # contenidos no verificados solo para que pase el test.
                    with self.assertRaises((RuntimeError, ValueError)):
                        editorial.seleccionado("","largo")

                # Una subida real salta el primer tema de SOLO este formato.
                hist.write_text(json.dumps([
                    {"tema_id": cola_short[0], "formato": "short", "estado": "subido"}
                ]), encoding="utf-8")
                siguiente=editorial.seleccionado("","short")
                self.assertEqual(siguiente["id"],cola_short[1])
                if cola_largo:
                    self.assertEqual(editorial.seleccionado("","largo")["id"],cola_largo[0])
                else:
                    with self.assertRaises((RuntimeError, ValueError)):
                        editorial.seleccionado("","largo")

    def test_plan_y_descripcion_primer_short(self):
        tema=self.nuevos[IDS[0]]
        texto,desc,plan=editorial.preparar_plan(tema,"short")
        self.assertGreater(len(texto.split()),40)
        self.assertFalse(plan["publicacion_automatica"])
        self.assertIn("rockstargames.com",desc)


if __name__=="__main__":
    unittest.main()
