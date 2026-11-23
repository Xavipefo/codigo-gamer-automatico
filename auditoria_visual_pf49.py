#!/usr/bin/env python3
"""PF-49: auditoría independiente de imágenes oficiales antes de YouTube.

Comprueba el catálogo de fotogramas REAL exportado, no solo el plan.
Las escenas sobre una región concreta no pueden contener imágenes de otra.
No certifica visualmente el contenido por píxeles: revisión humana pendiente.
"""
import json
from pathlib import Path
from rockstar_media import categoria, region_explicita

BASE=Path(__file__).resolve().parent

def evaluar(plan,manifiesto):
    errores=[]
    avisos=[]
    exclusivas=plan.get("categorias_visuales_exclusivas") or []
    escenas=manifiesto.get("escenas",[])
    if not isinstance(escenas,list) or not escenas:
        errores.append("Falta el manifiesto de escenas")
        escenas=[]
    fotos=[s for s in escenas if s.get("tipo")=="foto"]
    if not fotos:
        errores.append("El vídeo no utiliza ninguna fotografía verificable")
    for f in fotos:
        nombre=f.get("titulo","")
        if not nombre:
            errores.append("Imagen sin identificación en manifiesto")
            continue
        cat=categoria(nombre)
        if exclusivas and cat not in exclusivas:
            errores.append("Imagen "+nombre+" ajena a "+", ".join(exclusivas))
    guion=plan.get("escenas",[])
    # En Shorts, los planos suelen alinearse con el guion. Los largos
    # pueden tener 5-10 planos por sección; no fingir sincronización.
    if len(guion)==len(escenas):
        for g,m in zip(guion,escenas):
            region=region_explicita(g.get("texto",""))
            if region and m.get("tipo")=="foto" and categoria(m.get("titulo",""))!=region:
                errores.append("Escena sobre "+region+" ilustrada con "+str(m.get("titulo","")))
    else:
        avisos.append("El número de planos no coincide con las frases; "
                      "revisión de sincronización visual humana pendiente")
    return {
        "version":"PF-49","estado":"bloqueado" if errores else "apto_para_revision_privada",
        "errores":errores,"avisos":avisos,
        "fotografias":len(fotos),
        "publicacion_publica_automatica":False,
        "revision_humana_pendiente":True,
    }

def main():
    plan=json.loads((BASE/"salida/plan.json").read_text(encoding="utf-8"))
    manifiesto=json.loads((BASE/"salida/revision_visual/manifiesto_escenas.json").read_text(encoding="utf-8"))
    informe=evaluar(plan,manifiesto)
    destino=BASE/"salida/informe_qa_pf49.json"
    destino.write_text(json.dumps(informe,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(informe,ensure_ascii=False),flush=True)
    if informe["errores"]:
        raise SystemExit("PF-49: imágenes ajenas al guion; bloquear subida")

if __name__=="__main__":
    main()
