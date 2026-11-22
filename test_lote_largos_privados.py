"""PF-43: nuevo lote de largos, sin conectarse a GitHub ni YouTube."""
import json
import os
import tempfile
import unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch

from lote_largos_privados import planificar,reservar,lanzar

ROOT=Path(__file__).resolve().parent


class LotesLargosPrivados(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)
        datos=json.loads((ROOT/"temas_verificados.json").read_text(encoding="utf-8"))
        largos=[x for x in datos if x.get("id") in (
            "gta6-escenas-leonida-sin-spoilers",
            "gta6-vice-city-escena-musical",
            "gta6-fin-semana-oficial-20261122"
        )]
        (self.path/"temas_verificados.json").write_text(json.dumps(largos),encoding="utf-8")
        (self.path/"historial_publicados.json").write_text(json.dumps([
            {"tema_id":"gta6-fin-semana-oficial-20261122",
             "formato":"largo","estado":"subido"}
        ]),encoding="utf-8")
        (self.path/"reservas_largos.json").write_text("[]",encoding="utf-8")
        self.ahora=datetime(2026,11,22,18,tzinfo=timezone.utc)

    def test_selecciona_dos_largos_no_usados(self):
        p=planificar(2,raiz=self.path,ahora=self.ahora)
        self.assertEqual(p["temas"],[
            "gta6-escenas-leonida-sin-spoilers",
            "gta6-vice-city-escena-musical"
        ])
        self.assertEqual(p["privacidad"],"private")
        self.assertFalse(p["publicacion_publica"])

    def test_prohibe_duplica_y_ids_desconocidos(self):
        with self.assertRaises(ValueError):
            planificar(3,raiz=self.path,ahora=self.ahora)
        with self.assertRaises(ValueError):
            planificar(2,"gta6-vice-city-escena-musical|gta6-vice-city-escena-musical",
                       raiz=self.path,ahora=self.ahora)
        with self.assertRaises(ValueError):
            planificar(1,"gta6-tema-inventado",raiz=self.path,ahora=self.ahora)

    def test_reservas_evitan_duplicados_y_expiran(self):
        p=planificar(1,raiz=self.path,ahora=self.ahora)
        reservar(p,raiz=self.path)
        otro=planificar(1,raiz=self.path,ahora=self.ahora)
        self.assertNotEqual(otro["temas"],p["temas"])
        de_nuevo=planificar(1,raiz=self.path,ahora=self.ahora+timedelta(hours=73))
        self.assertEqual(de_nuevo["temas"],p["temas"])

    def test_sin_consentimiento_no_despacha(self):
        p=planificar(1,raiz=self.path,ahora=self.ahora)
        with patch.dict(os.environ,{"PF_CONFIRMACION":"NO_EJECUTAR",
                                     "GH_TOKEN":"test","GH_REPO":"Xavipefo/codigo-gamer-automatico"}):
            with self.assertRaises(PermissionError):
                lanzar(p,runner=lambda *_a,**_k:None)

    def test_despacho_solo_privado_sin_shell(self):
        p=planificar(2,raiz=self.path,ahora=self.ahora)
        comandos=[]
        class Resultado:
            returncode=0
            stderr=""
        def falso(args,**opts):
            self.assertNotIn("shell",opts)
            comandos.append(args)
            return Resultado()
        with patch.dict(os.environ,{"PF_CONFIRMACION":"GENERAR_PRIVADO",
                                     "GH_TOKEN":"demo","GH_REPO":"Xavipefo/codigo-gamer-automatico"}):
            enviados=lanzar(p,runner=falso)
        self.assertEqual(enviados,p["temas"])
        self.assertEqual(len(comandos),2)
        self.assertTrue(all("crear_largo_privado.yml" in x for x in comandos))
        self.assertTrue(all("--public" not in x for row in comandos for x in row))


if __name__=="__main__":
    unittest.main()
