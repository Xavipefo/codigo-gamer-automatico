"""Pruebas de resiliencia Gemini: no usan API, ni consumen cuota."""
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from gemini_reintentos import solicitar_json


def http_error(code):
    return urllib.error.HTTPError(
        "https://generativelanguage.googleapis.com/test",
        code, "simulated", {}, None,
    )


class TestReintentosGemini(unittest.TestCase):
    def test_http503_recupera_tercer_intento(self):
        respuesta = io.BytesIO(json.dumps({"escenas": ["todo bien"]}).encode())
        with patch(
            "gemini_reintentos.urllib.request.urlopen",
            side_effect=[http_error(503), http_error(503), respuesta],
        ) as abrir, patch(
            "gemini_reintentos.time.sleep"
        ) as dormir, patch(
            "gemini_reintentos.random.uniform", return_value=0
        ):
            resultado = solicitar_json(
                "https://test.example/no-real-request",
                max_intentos=4, contexto="test"
            )
            self.assertEqual(resultado, {"escenas": ["todo bien"]})
            self.assertEqual(abrir.call_count, 3)
            self.assertEqual([x.args[0] for x in dormir.call_args_list], [2, 4])

    def test_http403_no_reintenta(self):
        with patch(
            "gemini_reintentos.urllib.request.urlopen",
            side_effect=http_error(403),
        ) as abrir, patch("gemini_reintentos.time.sleep") as dormir:
            with self.assertRaises(urllib.error.HTTPError) as fallo:
                solicitar_json("https://test.example", max_intentos=4)
            self.assertEqual(fallo.exception.code, 403)
            abrir.assert_called_once()
            dormir.assert_not_called()

    def test_http503_persistente_se_detiene_tras_cuatro(self):
        with patch(
            "gemini_reintentos.urllib.request.urlopen",
            side_effect=http_error(503),
        ) as abrir, patch(
            "gemini_reintentos.time.sleep"
        ) as dormir, patch(
            "gemini_reintentos.random.uniform", return_value=0
        ):
            with self.assertRaises(urllib.error.HTTPError):
                solicitar_json("https://test.example", max_intentos=4)
            self.assertEqual(abrir.call_count, 4)
            self.assertEqual(dormir.call_count, 3)

    def test_http429_hace_reintentos_limitados(self):
        respuesta = io.BytesIO(b'{"ok":true}')
        with patch(
            "gemini_reintentos.urllib.request.urlopen",
            side_effect=[http_error(429), respuesta],
        ) as abrir, patch(
            "gemini_reintentos.time.sleep"
        ), patch("gemini_reintentos.random.uniform", return_value=0):
            self.assertEqual(
                solicitar_json("https://test.example", max_intentos=2),
                {"ok": True},
            )
            self.assertEqual(abrir.call_count, 2)


if __name__ == "__main__":
    unittest.main()
