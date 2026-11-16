"""Pruebas de seguridad sin llamadas reales a YouTube ni subidas."""
import unittest
from unittest.mock import MagicMock
from subir_youtube_privado import rechazar_subida_duplicada


class PruebasSubidaSegura(unittest.TestCase):
    def crear_api_falsa(self, descripcion):
        api = MagicMock()
        api.channels().list().execute.return_value = {
            "items": [{
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "UU_fake_uploads"}
                }
            }]
        }
        api.playlistItems().list().execute.return_value = {
            "items": [{"contentDetails": {"videoId": "video_123"}}],
            "nextPageToken": None
        }
        api.videos().list().execute.return_value = {
            "items": [{
                "id": "video_123",
                "snippet": {"description": descripcion}
            }]
        }
        return api

    def test_bloquea_tema_previamente_subido(self):
        api = self.crear_api_falsa(
            "Fuentes oficiales\nIdentificador editorial: PF-ID:gta6-jason-lucia\n"
        )
        with self.assertRaisesRegex(RuntimeError, "ya existe"):
            rechazar_subida_duplicada(api, "gta6-jason-lucia")
        api.videos().insert.assert_not_called()

    def test_permite_tema_distinto(self):
        api = self.crear_api_falsa(
            "Fuentes oficiales\nIdentificador editorial: PF-ID:otro-tema\n"
        )
        rechazar_subida_duplicada(api, "gta6-jason-lucia")
        api.videos().insert.assert_not_called()

    def test_falla_si_no_puede_ver_lista_de_subidas(self):
        api = self.crear_api_falsa("")
        api.channels().list().execute.return_value = {"items": []}
        with self.assertRaisesRegex(RuntimeError, "canal autorizado"):
            rechazar_subida_duplicada(api, "gta6-jason-lucia")


if __name__ == "__main__":
    unittest.main()
