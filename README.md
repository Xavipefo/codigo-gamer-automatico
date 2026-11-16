# Código Gamer — automatización independiente

Proyecto para un futuro canal de videojuegos en español. **Estado: prototipo editorial v0.1.**

## Lo que hay en este repositorio

- `preparar_contenido.py`: prepara borradores de guion, descripción con fuentes y plan de escenas a partir de un archivo JSON de hechos.
- `temas_verificados.json`: dos temas iniciales de GTA VI basados en información de Rockstar Games, consultada el 16-11-2026.
- `test_preparar_contenido.py`: pruebas automáticas de validación básica.
- `.github/workflows/preparar_borrador.yml`: ejecución **exclusivamente manual** que comprueba el programa y entrega un artefacto descargable.

**Importante:** el script valida la estructura de los datos y que las URLs pertenezcan a dominios permitidos; **no** comprueba automáticamente que los enlaces funcionen ni que cada afirmación esté respaldada. La verificación editorial final sigue siendo humana.

## Ejecutar sin GitHub Actions

En una terminal con Python 3.11 o posterior:

```bash
python -m unittest discover -s . -p "test_*.py"
python preparar_contenido.py
```

Para otro tema: `python preparar_contenido.py --tema gta6-jason-lucia`.

Los resultados se escriben en `salida/guion.txt`, `salida/descripcion.txt` y `salida/plan.json`.

## Ejecutar desde GitHub

Abre **Actions** > **Codigo Gamer - Borrador manual** > **Run workflow**. Descarga el artefacto `codigo-gamer-borrador` al finalizar. El workflow no renderiza un MP4, no se conecta a YouTube y no publica contenido.

Este repositorio es **privado**. Las ejecuciones con GitHub-hosted runners pueden consumir minutos de la cuota del plan. Por eso no se ha configurado ninguna ejecución programada.

## Próximas fases

1. Curación de noticias con fuentes rastreables y detección de duplicados.
2. Motor local de guion con revisión de afirmaciones.
3. Generación de voz y montaje de Shorts originales.
4. Contenido largo con recursos audiovisuales propios o licenciados.
5. Subida **privada**, con autorización exclusiva del nuevo canal y revisión previa.

No se han copiado tokens, secretos ni automatizaciones de Dato Nebular ni Alerta Binaria. Antes de publicar automáticamente serán necesarias pruebas y configuración específicas de este canal.

## Fuentes de referencia

- https://www.rockstargames.com/VI
- https://www.rockstargames.com/newswire/article/ak3ak31a49a221/grand-theft-auto-vi-is-now-set-to-launch-november-19-2026
- https://www.rockstargames.com/newswire/article/5171972o3ak5oa/pre-order-grand-theft-auto-vi-on-june-25

## Prototipo MP4 (experimental)

Se ha añadido `generar_short.py` y el workflow manual **Codigo Gamer - Renderizar Short privado local**. Se puede ejecutar desde Actions > Run workflow. Genera un MP4 vertical de 720×1280 con tarjetas gráficas originales (sin gameplay de terceros) y una voz sintética Piper en español. El archivo se entrega como artefacto de GitHub; **no se sube a YouTube ni se publica**.

El workflow descarga dependencias y el modelo de voz y puede consumir minutos de Actions de este repositorio privado. La duración exacta y los resultados audiovisuales **aún no se han probado mediante una ejecución de render**. Se requiere revisión humana antes de considerar el material apto para publicación; las tarjetas son un primer prototipo visual, no la versión definitiva de gaming.

Los audios, escenas y referencias deben pasar la revisión editorial y de derechos de uso. El uso de voz sintética deberá cumplir las condiciones de su modelo y de la plataforma de distribución.
