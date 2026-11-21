"""PF-42: pruebas sin red de la auditoría de ritmo y variedad visual."""
import unittest
from control_calidad import validar_ritmo_pf42


def informe(**cambios):
    fotos = [
        {"titulo": f"Captura oficial {i}", "medio": "foto", "segundos": 3.0}
        for i in range(4)
    ]
    dato = {
        "version": "PF-41",
        "numero_planos": 4,
        "planos": fotos,
        "duracion_cierre_segundos": 3.0,
        "repeticiones_tts_adicionales": 0,
    }
    dato.update(cambios)
    return dato


class ControlRitmoPF42(unittest.TestCase):
    def test_permite_4_planos_distintos_con_cierre_corto(self):
        self.assertEqual(validar_ritmo_pf42(informe(), 15.0), 4)

    def test_rechaza_informe_con_contador_incorrecto(self):
        with self.assertRaisesRegex(ValueError, "contadores"):
            validar_ritmo_pf42(informe(numero_planos=5), 15.0)

    def test_rechaza_repeticion_de_unica_foto(self):
        repetidos = [
            {"titulo": "Misma captura", "medio": "foto", "segundos": 3.0}
            for _ in range(4)
        ]
        with self.assertRaisesRegex(ValueError, "única fotografía"):
            validar_ritmo_pf42(informe(planos=repetidos), 15.0)

    def test_rechaza_cierre_demasiado_largo(self):
        with self.assertRaisesRegex(ValueError, "cierre"):
            validar_ritmo_pf42(informe(duracion_cierre_segundos=9.0), 21.0)

    def test_rechaza_duracion_inconsistente(self):
        with self.assertRaisesRegex(ValueError, "no cuadran"):
            validar_ritmo_pf42(informe(), 22.0)

    def test_rechaza_narracion_duplicada(self):
        with self.assertRaisesRegex(ValueError, "duplicada"):
            validar_ritmo_pf42(informe(repeticiones_tts_adicionales=1), 15.0)


if __name__ == "__main__":
    unittest.main()
