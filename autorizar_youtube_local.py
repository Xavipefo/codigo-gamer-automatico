#!/usr/bin/env python3
"""Autoriza una cuenta de YouTube y obtiene JSON OAuth para guardar en GitHub Secrets.

EJECUTAR EN TU ORDENADOR, NUNCA EN GITHUB ACTIONS.
Requiere un OAuth Desktop Client JSON descargado desde Google Cloud Console.
"""
import argparse
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES=["https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--client-secrets",type=Path,required=True)
    p.add_argument("--out",type=Path,default=Path("youtube_oauth_privado.json"))
    args=p.parse_args()
    if not args.client_secrets.exists():
        raise ValueError("No se encuentra el OAuth client secret JSON descargado")
    flow=InstalledAppFlow.from_client_secrets_file(str(args.client_secrets),SCOPES)
    cred=flow.run_local_server(host="localhost",port=0,open_browser=True,
                               access_type="offline",prompt="consent")
    if not cred.refresh_token:
        raise RuntimeError("Google no devolvió refresh_token: revisa consentimiento y scopes")
    args.out.write_text(cred.to_json()+"\n",encoding="utf-8")
    print("Credencial guardada LOCALMENTE en:",args.out)
    print("Copia el JSON completo a GitHub Secret YOUTUBE_OAUTH_JSON")
    print("No publiques, subas ni compartas nunca este archivo.")
    print("Confirma el ID real del canal desde YouTube Studio > Configuración > Canal > Avanzada.")


if __name__=="__main__":
    main()
