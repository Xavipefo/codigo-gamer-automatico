"""PF-92: pruebas del plan de tres meses y de la historia en su propia cola.

No consulta servicios externos ni sube vídeos. Valida también la retirada
segura tras una subida privada simulada.
"""
import json
import os
import tempfile
import unittest
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import editorial
import cola_editorial_pf as ce
import registrar_subida as registro

BASE=Path(__file__).resolve().parent
COMPARATIVA="gta6-vs-gtav-comparativa-profunda-20261124"

def leer(relative):
    return json.loads((BASE/relative).read_text(encoding="utf-8"))

class ProgramaPF92(unittest.TestCase):
    def test_proximo_largo_es_comparativa_profunda(self):
        docs=ce.cargar("largo")
        historial=leer("historial_publicados.json")
        ya_subido=any(x.get("tema_id")==COMPARATIVA and x.get("formato")=="largo"
                      and x.get("estado") in ("subido","publicado") for x in historial)
        self.assertTrue(ya_subido or (docs and docs[0]==COMPARATIVA),
                        "La comparativa debe estar en primer lugar o subida en privado")
        temas={x["id"]:x for x in leer("temas_verificados.json")}
        t=temas[COMPARATIVA]
        self.assertEqual(len(t["escenas_largas"]),24)
        self.assertGreaterEqual(len(t["hechos"]),10)
        self.assertGreaterEqual(len(t["titulos_experimento"]),3)
        self.assertGreaterEqual(len(t["miniatura_opciones"]),3)
        self.assertGreater(len(" ".join(t["escenas_largas"]).split()),2200)
        guion,_,plan=editorial.preparar_plan(t,"largo")
        self.assertFalse(plan["requiere_guion_ia"])
        self.assertEqual(plan["duracion_objetivo_segundos"],[900,1500])
        self.assertTrue(plan["documental_profundo"])
        self.assertGreater(len(guion.split()),2200)
        self.assertFalse(plan["publicacion_automatica"])

    def test_92_episodios_cronologicos_y_no_inventados(self):
        serie=leer("series/historia_gtavi_92_dias.json")
        epis=serie["episodios"]
        self.assertEqual(len(epis),92)
        self.assertEqual(len({x["id"] for x in epis}),92)
        first=date(2026,11,24)
        for i,ep in enumerate(epis):
            self.assertEqual(ep["episodio"],i+1)
            self.assertEqual(ep["fecha_objetivo"],(first+timedelta(days=i)).isoformat())
            self.assertEqual(ep["hora_objetivo"],"14:30")
            self.assertFalse(ep["publicacion_automatica"])
            if i:
                self.assertTrue(ep["spoilers"])
                if ep["id"] in ("historia-gtavi-002", "historia-gtavi-003"):
                    self.assertEqual(ep["estado"],"confirmado_fuentes_oficiales_y_guias")
                    self.assertFalse(ep["licencia_video_requerida"])
                    self.assertIn("ilustrativas",ep["visual"])
                else:
                    self.assertEqual(ep["estado"],"pendiente_verificacion_gameplay")
        # La cola se consume realmente después de subir cada episodio.
        restantes=ce.cargar("historia")
        usados={x.get("tema_id") for x in leer("historial_publicados.json")
                if x.get("formato")=="short"
                and x.get("estado") in ("subido","publicado")}
        self.assertTrue(all(x not in usados for x in restantes))
        self.assertTrue(all(x in {e["id"] for e in epis} for x in restantes))

    def test_354_slots_y_distribucion_formato(self):
        cal=leer("colas/calendario_3meses.json")
        slots=cal["slots"]
        self.assertEqual(len(slots),354)
        self.assertEqual(sum(x["formato"]=="short" for x in slots),302)
        self.assertEqual(sum(x["formato"]=="largo" for x in slots),52)
        self.assertEqual(sum(x.get("linea_editorial")=="historia" for x in slots),92)
        self.assertEqual(sum(x.get("linea_editorial")=="general" for x in slots),210)
        self.assertEqual(len(leer("colas/programa_shorts_generales_210.json")),210)
        self.assertEqual(len(leer("colas/programa_documentales_50.json")),50)
        byday=Counter(x["fecha"] for x in slots if x["formato"]=="short")
        self.assertEqual(len(byday),92)
        for day,number in byday.items():
            dow=date.fromisoformat(day).weekday()
            self.assertEqual(number,4 if dow in (4,5) else 3)
            historia=[x for x in slots if x["fecha"]==day and x.get("linea_editorial")=="historia"]
            self.assertEqual(len(historia),1)
            self.assertEqual(historia[0]["hora"],"14:30")
        primeros=[x for x in slots if x["formato"]=="largo"]
        self.assertEqual(primeros[0]["tema_id"],COMPARATIVA)
        self.assertEqual(primeros[0]["estado"],"tema_confirmado")
        self.assertTrue(all(x["publicacion_automatica"] is False for x in slots))

    def test_las_tres_colas_son_independientes(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp=Path(tmp)
            (temp/"colas").mkdir()
            (temp/"colas"/"historia_shorts.json").write_text('["historia-001"]',encoding="utf-8")
            (temp/"colas"/"shorts.json").write_text('["otro-001"]',encoding="utf-8")
            (temp/"colas"/"documentales.json").write_text('["largo-001"]',encoding="utf-8")
            self.assertTrue(ce.retirar_por_video("short","historia-001",base=temp))
            self.assertEqual(ce.cargar("historia",temp),[])
            self.assertEqual(ce.cargar("short",temp),["otro-001"])
            self.assertEqual(ce.cargar("largo",temp),["largo-001"])

    def test_seleccion_automatica_historias_sin_afectar_general(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"historial.json"
            path.write_text("[]",encoding="utf-8")
            with patch.object(editorial,"HISTORIAL",path),patch.object(
                    editorial,"_banco_para_preflight",return_value=None):
                with patch.dict(os.environ,{"PF_LINEA_EDITORIAL":"historia"}):
                    historias=ce.cargar("historia")
                    if historias:
                        seleccionado=editorial.seleccionado("","short")
                        self.assertEqual(seleccionado["id"],historias[0])
                    else:
                        with self.assertRaises(RuntimeError):
                            editorial.seleccionado("","short")
                with patch.dict(os.environ,{"PF_LINEA_EDITORIAL":"general"}):
                    seleccionado=editorial.seleccionado("","short")
                    self.assertEqual(seleccionado["id"],ce.cargar("short")[0])
                with patch.dict(os.environ,{"PF_LINEA_EDITORIAL":"historia"}):
                    with self.assertRaises(ValueError):
                        editorial.seleccionado("","largo")

    def test_registro_privado_retira_solo_episodio_correspondiente(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            out=root/"salida"
            colas=root/"colas"
            out.mkdir()
            colas.mkdir()
            (root/"historial_publicados.json").write_text("[]",encoding="utf-8")
            (colas/"historia_shorts.json").write_text('["historia-gtavi-001","historia-gtavi-002"]',encoding="utf-8")
            (colas/"shorts.json").write_text('["short-normal"]',encoding="utf-8")
            data={"estado":"subido","privacidad_verificada":"private",
                  "tema_id":"historia-gtavi-001","formato":"short",
                  "video_id":"pf92-ficticio"}
            (out/"youtube_resultado.json").write_text(json.dumps(data),encoding="utf-8")
            with patch.object(registro,"OUT",out),patch.object(
                    registro,"HISTORIAL",root/"historial_publicados.json"),patch.object(
                    ce,"BASE",root):
                registro.main()
            self.assertEqual(json.loads((colas/"historia_shorts.json").read_text()),["historia-gtavi-002"])
            self.assertEqual(json.loads((colas/"shorts.json").read_text()),["short-normal"])

if __name__=="__main__":
    unittest.main()
