"""Fotos propias/IA y de terceros: exigir derechos y citar fuente."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from visuales_autorizados import catalogo, creditos_para_descripcion, escena_con_foto


class TestFotosConLicencia(unittest.TestCase):
    def test_sin_credenciales_no_hay_descarga(self):
        with patch.dict(os.environ, {"PF_IMAGENES_JSON": ""}):
            self.assertEqual(catalogo("gta6"), [])
            self.assertEqual(creditos_para_descripcion("gta6"), [])

    def test_rechaza_sin_derechos(self):
        dato = {"gta6": [{
            "url":"https://example.org/test.jpg", "derechos_confirmados":False,
            "origen":"oficial_autorizado", "credito":"Propietario",
            "fuente_publica":"https://example.org/creditos",
        }]}
        with patch.dict(os.environ, {"PF_IMAGENES_JSON": json.dumps(dato)}):
            with self.assertRaisesRegex(ValueError, "derechos"):
                catalogo("gta6")

    def test_exige_tipo_y_atribucion_publica(self):
        base = {
            "url":"https://example.org/test.jpg", "derechos_confirmados":True,
            "origen":"ia_original", "credito":"Diseño original del canal",
            "fuente_publica":"https://example.org/creditos",
        }
        with patch("visuales_autorizados._validar_url_descarga") as validar:
            with patch.dict(os.environ, {"PF_IMAGENES_JSON": json.dumps({"gta6":[base]})}):
                self.assertEqual(
                    creditos_para_descripcion("gta6"),
                    ["Diseño original del canal — https://example.org/creditos"]
                )
                validar.assert_called_once()
            base["origen"]="sin_licencia"
            with patch.dict(os.environ, {"PF_IMAGENES_JSON": json.dumps({"gta6":[base]})}):
                with self.assertRaises(ValueError):
                    catalogo("gta6")

    def test_imagen_real_con_texto_y_credito(self):
        with tempfile.TemporaryDirectory() as t:
            foto=Path(t)/"fuente.png"
            Image.new("RGB",(1280,720),(90,140,175)).save(foto)
            salida=Path(t)/"fotograma.png"
            escena_con_foto(
                {"texto":"Detalles de Vice City y Leonida comprobados por Rockstar."},
                "largo",foto,"Titular de la imagen",salida
            )
            self.assertTrue(salida.exists())
            with Image.open(salida) as im:
                self.assertEqual(im.size,(1280,720))


if __name__ == "__main__":
    unittest.main()
