"""PF-46: nunca sustituir Vice City por imágenes de otra zona al elegir cola."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import editorial

RAIZ=Path(__file__).resolve().parent

class PreflightVisualPF46(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=json.loads((RAIZ/"temas_verificados.json").read_text(encoding="utf-8"))
        cls.vice=next(t for t in data if t["id"]=="gta6-vice-city-fotos-oficiales")
        cls.leonida=next(t for t in data if t["id"]=="gta6-leonida-keys-fotos")

    def test_rechaza_banco_vice_insuficiente(self):
        banco={"imagenes":[
            {"archivo":f"vice_{i}.jpg","categoria":"vice"} for i in range(4)
        ]+[{"archivo":f"port_{i}.jpg","categoria":"port"} for i in range(40)]}
        self.assertFalse(editorial._cobertura_visual_exclusiva(
            self.vice,"short",banco))
        self.assertFalse(editorial._cobertura_visual_exclusiva(
            self.leonida,"short",banco))

    def test_no_descarta_imagenes_suficientes_del_tema(self):
        _,_,plan=editorial.preparar(self.vice)
        n=max(5,len(plan["escenas"]))
        banco={"imagenes":[
            {"archivo":f"vice_{i}.jpg","categoria":"vice"} for i in range(n)
        ]}
        self.assertTrue(editorial._cobertura_visual_exclusiva(
            self.vice,"short",banco))

    def test_automatico_salta_tema_insuficiente_no_lo_repite(self):
        banco={"imagenes":[{"archivo":"uno.jpg","categoria":"vice"}]+[
            {"archivo":f"keys_{i}.jpg","categoria":"leonida"} for i in range(7)
        ]}
        with patch.object(editorial,"cargar_elegibles",return_value=[
                self.vice,self.leonida]),patch.object(
                editorial,"cargar_historial",return_value=[]),patch.object(
                editorial,"_banco_para_preflight",return_value=banco):
            elegido=editorial.seleccionado("","short")
            self.assertEqual(elegido["id"],self.leonida["id"])
            # Si el usuario pide explícitamente el tema, su auditoría
            # de producción se ocupará de bloquear el banco escaso.
            elegido=editorial.seleccionado(self.vice["id"],"short")
            self.assertEqual(elegido["id"],self.vice["id"])

    def test_sin_banco_carga_plan_y_control_posterior(self):
        self.assertTrue(editorial._cobertura_visual_exclusiva(
            self.vice,"short",None))

if __name__=="__main__":
    unittest.main()
