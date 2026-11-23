"""Regresión PF-41: la serie Historia GTA VI debe renderizar capturas
oficiales y el QA debe exigir EXACTAMENTE el informe que genera el motor.
"""
import unittest
from politica_visual_pf import modo_rockstar, requiere_informe_pf41

class TestHistoriaPF41(unittest.TestCase):
    def test_episodio_historia_activa_fotos_e_informe(self):
        plan={"tema_id":"historia-gtavi-001",
              "estilo_retencion":"PF-41-ganchos-directos-planos-3s"}
        self.assertTrue(modo_rockstar(plan["tema_id"],"1"))
        self.assertTrue(requiere_informe_pf41(plan,"short","1"))

    def test_shorts_gta6_tradicionales_siguen_iguales(self):
        plan={"tema_id":"gta6-port-gellhorn-galeria",
              "estilo_retencion":"PF-41-ganchos-directos-planos-3s"}
        self.assertTrue(modo_rockstar(plan["tema_id"],"1"))
        self.assertTrue(requiere_informe_pf41(plan,"short","1"))

    def test_no_exigir_informe_si_montaje_no_lo_genera(self):
        for ident in ("otros-juegos-001","historia-otro-juego-001",""):
            plan={"tema_id":ident,
                  "estilo_retencion":"PF-41-ganchos-directos-planos-3s"}
            self.assertFalse(modo_rockstar(ident,"1"))
            self.assertFalse(requiere_informe_pf41(plan,"short","1"))
        plan={"tema_id":"historia-gtavi-001",
              "estilo_retencion":"PF-41-ganchos-directos-planos-3s"}
        self.assertFalse(modo_rockstar(plan["tema_id"],"0"))
        self.assertFalse(requiere_informe_pf41(plan,"short","0"))
        self.assertFalse(requiere_informe_pf41(plan,"largo","1"))

    def test_no_desactivar_control_si_faltan_los_datos(self):
        plan={"tema_id":"historia-gtavi-001",
              "estilo_retencion":"PF-41-ganchos-directos-planos-3s"}
        self.assertTrue(requiere_informe_pf41(plan,"short","1"))
        # La presencia, duración, fuentes y diversidad de los subplanos
        # siguen siendo comprobadas por control_calidad.py.
        import inspect
        import control_calidad
        s=inspect.getsource(control_calidad.comprobar)
        self.assertIn("falta informe de subplanos",s)
        self.assertIn("validar_ritmo_pf42",s)

if __name__=="__main__":
    unittest.main()
