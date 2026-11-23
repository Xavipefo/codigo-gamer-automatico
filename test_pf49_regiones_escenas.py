"""PF-49: ninguna frase sobre una región concreta muestra otra región."""
import unittest
from pathlib import Path
from unittest.mock import patch

import rockstar_media as media

class PruebasPF49(unittest.TestCase):
    def test_regiones_concretas_y_comparaciones(self):
        casos={
            "En Vice City se ven rascacielos":"vice",
            "Las playas de Leonida Keys aparecen en imágenes":"leonida",
            "Port Gellhorn muestra nuevas calles":"port",
            "El parque Mount Kalaga":"kalaga",
            "Grassrivers se menciona en la guía":"grassrivers",
            "Ambrosia es otra región":"ambrosia",
            "Vice City y Leonida Keys son regiones distintas":None,
            "El estado de Leonida tiene zonas distintas":None,
        }
        for frase,categoria in casos.items():
            self.assertEqual(media.region_explicita(frase),categoria,frase)

    def test_plan_largo_multi_region_usa_fotografia_correcta_por_frase(self):
        imagenes=[
            {"archivo":f"{cat}_{i}.jpg","categoria":cat,
             "nombre":f"{cat}_{i}"}
            for cat in ("vice","leonida","port","ambrosia","kalaga","grassrivers")
            for i in range(3)
        ]
        escenas=[
            {"texto":"Las calles de Vice City aparecen en la galería oficial."},
            {"texto":"Las islas Leonida Keys aparecen en el mapa."},
            {"texto":"Port Gellhorn tiene otro carácter."},
            {"texto":"Mount Kalaga presenta zonas naturales."},
            {"texto":"Ambrosia es otra localización de la región."},
            {"texto":"Grassrivers contiene humedales."},
        ]
        with patch.object(media,"cargar_banco",return_value={"imagenes":imagenes}):
            elegidas=media.elegir_imagenes(
                {"titulo_propuesto":"Seis regiones de GTA VI",
                 "visuales_preferidos":["vice","leonida","port"]},
                escenas,Path("/tmp"))
        categorias=[media.region_explicita(x["texto"]) for x in escenas]
        self.assertEqual([e[2].split("_")[0] for e in elegidas],categorias)

    def test_no_sustituye_vice_city_por_port_gellhorn(self):
        imagenes=[{"archivo":"port.jpg","categoria":"port",
                   "nombre":"Port_Gellhorn_01"}]
        with patch.object(media,"cargar_banco",return_value={"imagenes":imagenes}):
            with self.assertRaisesRegex(RuntimeError,"faltan fotografías"):
                media.elegir_imagenes(
                    {"titulo_propuesto":"Vice City"},
                    [{"texto":"Vista de Vice City"}],Path("/tmp"))

if __name__=="__main__":
    unittest.main()
