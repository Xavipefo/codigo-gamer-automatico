#!/usr/bin/env python3
"""Smoke test sin APIs ni YouTube: renderiza un Short con capturas Rockstar reales.

Solo se usa en GitHub Actions para comprobar las imágenes del montaje.
El audio son silencios sintéticos. No se exporta ni se publica el MP4.
"""
import hashlib
import json
import os
import wave
from pathlib import Path
from unittest.mock import patch

import motor_video

FRASES = [
    ("gancho", "Estas son las primeras claves visuales de Grand Theft Auto VI que Rockstar ha mostrado en su página oficial."),
    ("hecho_verificado", "Jason y Lucia protagonizan varios de los materiales oficiales que acompañan al esperado lanzamiento del videojuego."),
    ("contexto", "Vice City aparece en distintas capturas y muestra tanto las zonas urbanas como el ambiente costero."),
    ("hecho_verificado", "Leonida incluye escenarios que se aprecian en la galería oficial, con vistas de diferentes paisajes del juego."),
    ("hecho_verificado", "Las imágenes oficiales permiten comparar personajes, localizaciones y detalles sin inventar información sobre mecánicas."),
    ("cierre", "Puedes consultar las fuentes originales de Rockstar para descubrir las capturas y conocer más detalles del lanzamiento."),
]

class NarradorDePrueba:
    voz = "Ryan"
    voz_real = "Silencio de prueba (sin TTS)"
    proveedor = "test"
    peticiones = 0
    recuperados = 0

    def __init__(self, formato, plan):
        self.peticiones = 0

    def narrar(self, texto, destino):
        self.peticiones += 1
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destino), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(b"\0\0" * (24000 * 3))
        return 3.0

def main():
    texto = " ".join(frase for _,frase in FRASES)
    plan = {
        "canal": "Píxel Feroz",
        "tema_id": "gta6-jason-lucia-vice-city",
        "titulo_propuesto": "GTA VI: capturas oficiales de Rockstar",
        "texto_miniatura": "NUEVAS CAPTURAS GTA 6",
        "formato": "short",
        "estado": "BORRADOR_PENDIENTE_REVISION",
        "publicacion_automatica": False,
        "escenas": [{"tipo": tipo, "texto":frase} for tipo,frase in FRASES],
        "huella_guion":hashlib.sha256(texto.encode()).hexdigest(),
    }
    salida = motor_video.SALIDA
    salida.mkdir(parents=True, exist_ok=True)
    (salida/"descripcion.txt").write_text(
        "Prueba de montaje sin publicar\nFuente: https://www.rockstargames.com/VI/media\n",
        encoding="utf-8"
    )
    with patch.object(motor_video, "NarradorGemini", NarradorDePrueba), patch.object(
        motor_video, "estimar_consumo", lambda *args: None
    ):
        motor_video.montar(plan,texto)
    manifest = json.loads((salida/"revision_visual/manifiesto_escenas.json").read_text())
    escenas = manifest["escenas"]
    fotos = [s for s in escenas if s["tipo"]=="foto"]
    if len(escenas) < 6 or len(fotos) < 5:
        raise RuntimeError(f"No se han renderizado suficientes imágenes: {len(fotos)}")
    print("SMOKE TEST REAL: escenas",len(escenas),"fotos oficiales",len(fotos),flush=True)

if __name__=="__main__":
    main()
