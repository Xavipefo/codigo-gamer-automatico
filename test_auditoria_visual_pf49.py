"""PF-49: regresión de mosaicos reales con regiones mezcladas."""
import unittest
from auditoria_visual_pf49 import evaluar

class AuditoriaPF49(unittest.TestCase):
    def test_bloquea_vice_city_y_ambrosia_en_short_leonida_keys(self):
        plan={"categorias_visuales_exclusivas":["leonida"],
              "escenas":[{"texto":"La fauna de Leonida Keys"}]}
        fotos=[{"tipo":"foto","titulo":x} for x in [
            "Leonida_Keys_04","Leonida_Keys_06",
            "Brian_Heder_03","Vice_City_22","Ambrosia_06"
        ]]
        reporte=evaluar(plan,{"escenas":fotos})
        self.assertEqual(reporte["estado"],"bloqueado")
        self.assertTrue(any("Vice_City" in x for x in reporte["errores"]))

    def test_no_falla_banco_exclusivo_correcto(self):
        plan={"categorias_visuales_exclusivas":["leonida"],
              "escenas":[{"texto":"Las islas de Leonida Keys"}]}
        reporte=evaluar(plan,{"escenas":[
            {"tipo":"foto","titulo":"Leonida_Keys_01"},
            {"tipo":"foto","titulo":"Leonida_Keys_02"}]})
        self.assertEqual(reporte["estado"],"apto_para_revision_privada")
        self.assertFalse(reporte["errores"])
        self.assertTrue(reporte["revision_humana_pendiente"])

    def test_rechaza_foto_ajena_a_frase_alineada(self):
        plan={"escenas":[{"texto":"Vice City es una región del mapa"}]}
        reporte=evaluar(plan,{"escenas":[
            {"tipo":"foto","titulo":"Port_Gellhorn_01"}]})
        self.assertTrue(reporte["errores"])
        self.assertFalse(reporte["publicacion_publica_automatica"])

if __name__=="__main__":
    unittest.main()
