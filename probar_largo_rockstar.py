#!/usr/bin/env python3
"""Prueba visual REAL de largo, sin TTS externa ni subida a YouTube.

Utiliza capturas oficiales ya descargadas. No publica audio, MP4 ni guion.
"""
import hashlib
import json
import os
import wave
from pathlib import Path
from unittest.mock import patch
import motor_video

FRASES=[
    ("gancho","Esta es una presentación editorial de Grand Theft Auto seis con datos oficiales confirmados y varias imágenes diferentes del juego, sin afirmar experiencias que todavía no hemos comprobado."),
    ("hecho_verificado","Rockstar muestra a Jason y Lucia en Vice City y el estado de Leonida. La galería oficial incluye muchas localizaciones y diferentes personajes, por eso cambiamos de plano cada pocos segundos."),
    ("cierre","La descripción incluye enlaces a las fuentes originales de Rockstar Games. Antes de publicar un vídeo sobre el lanzamiento necesitamos revisar qué hechos son realmente oficiales y cuáles siguen sin confirmarse."),
]
class NarradorSimulado:
    voz="Charon"
    voz_real="Narración sintética de prueba, solo silencio"
    proveedor="test"
    recuperados=0
    def __init__(self,formato,plan):
        self.peticiones=0
    def narrar(self,texto,archivo):
        self.peticiones+=1
        Path(archivo).parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(archivo),"wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(bytes(24000*2*16))
        return 16.0

def main():
    escenas=[{"tipo":tipo,"texto":texto} for tipo,texto in FRASES]
    guion=" ".join(x["texto"] for x in escenas)
    destino=Path("salida/prueba_largo")
    destino.mkdir(parents=True,exist_ok=True)
    (destino/"descripcion.txt").write_text(
        "Material verificado de Rockstar. Fuente: https://www.rockstargames.com/VI\n",
        encoding="utf-8"
    )
    plan={
        "canal":"Píxel Feroz","formato":"largo",
        "tema_id":"gta6-prueba-largo",
        "titulo_propuesto":"GTA VI: prueba visual de largo",
        "texto_miniatura":"GTA VI IMÁGENES REALES",
        "estado":"BORRADOR_PENDIENTE_REVISION",
        "publicacion_automatica":False,
        "narrador_voz":"Charon",
        "huella_guion":hashlib.sha256(guion.encode("utf-8")).hexdigest(),
        "visuales_preferidos":["jason","lucia","vice","leonida"],
        "escenas":escenas
    }
    with patch.object(motor_video,"SALIDA",destino),patch.object(
        motor_video,"NarradorGemini",NarradorSimulado
    ),patch.object(motor_video,"estimar_consumo",lambda *a:None),patch.dict(
        os.environ,{"PF_TTS_PROVIDER":"gemini","PF_ROCKSTAR_MEDIA":"1",
                    "PF_ROCKSTAR_CLIPS":"0"}
    ):
        motor_video.montar(plan,guion)
    manifest=json.loads(
        (destino/"revision_visual"/"manifiesto_escenas.json").read_text(encoding="utf-8")
    )
    tomas=manifest["escenas"]
    if len(tomas)<6 or sum(x["tipo"]=="foto" for x in tomas)<6:
        raise RuntimeError("Largo sin suficientes fotografías o cortes")
    if "Fuente oficial" not in (destino/"descripcion.txt").read_text(encoding="utf-8"):
        raise RuntimeError("Faltan créditos de Rockstar")
    print("LARGO REAL VALIDADO:",len(tomas),"subplanos en 48 segundos, sin subir",flush=True)

if __name__=="__main__":
    main()
