"""El lote solo procesa temas verificados y jamás publica en abierto."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import lote_shorts_privados as lote


class TestLotePrivado(unittest.TestCase):
    def test_cantidad_limitada(self):
        with self.assertRaises(ValueError):
            lote.producir(0)
        with self.assertRaises(ValueError):
            lote.producir(7)
        with self.assertRaises(ValueError):
            lote.producir(-1)

    def test_sin_oauth_no_hay_subida(self):
        with patch.dict(os.environ, {
            "PF_SUBIR_PRIVADO": "SI",
            "PF_TTS_PROVIDER": "qwen",
            "YOUTUBE_OAUTH_JSON": "",
        }):
            with self.assertRaisesRegex(RuntimeError, "YOUTUBE_OAUTH_JSON"):
                lote.comprobar_configuracion()

    def test_el_lote_exige_voz_local_y_privada(self):
        with patch.dict(os.environ, {
            "PF_SUBIR_PRIVADO": "NO",
            "PF_TTS_PROVIDER": "qwen",
            "YOUTUBE_OAUTH_JSON": "token-simulacro",
        }):
            with self.assertRaisesRegex(RuntimeError, "PRIVADA"):
                lote.comprobar_configuracion()
        with patch.dict(os.environ, {
            "PF_SUBIR_PRIVADO": "SI",
            "PF_TTS_PROVIDER": "gemini",
            "YOUTUBE_OAUTH_JSON": "token-simulacro",
        }):
            with self.assertRaisesRegex(RuntimeError, "Ryan"):
                lote.comprobar_configuracion()

    def test_cada_short_se_registra_antes_del_siguiente(self):
        eventos = []
        temas = iter([{"id": "gta6-uno"}, {"id": "gta6-dos"}])
        resultados = iter([
            {"tema_id":"gta6-uno","video_id":"video1","miniatura_confirmada":True},
            {"tema_id":"gta6-dos","video_id":"video2","miniatura_confirmada":True},
        ])
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "PF_SUBIR_PRIVADO": "SI",
            "PF_TTS_PROVIDER": "qwen",
            "YOUTUBE_OAUTH_JSON": "token-simulacro",
        }), patch.object(lote, "SALIDA", Path(tmp)/"salida"), patch.object(
            lote, "seleccionado", side_effect=lambda *a: next(temas)
        ), patch.object(
            lote, "estado_youtube", side_effect=lambda: next(resultados)
        ), patch.object(
            lote, "registrar_y_guardar",
            side_effect=lambda r: eventos.append("registro:" + r["tema_id"])
        ):
            def simular(*cmd):
                eventos.append("proceso:" + " ".join(cmd[1:]))
            salida = lote.producir(2, lanzar=simular)
            self.assertEqual(salida, ["video1", "video2"])
            primero = eventos.index("registro:gta6-uno")
            segundo = next(i for i,e in enumerate(eventos)
                           if e.startswith("proceso:editorial.py")
                           and "gta6-dos" in e)
            self.assertLess(primero, segundo)


if __name__ == "__main__":
    unittest.main()
