# Píxel Feroz — sistema independiente de YouTube

**Estado actual:** el código del sistema está preparado, pero faltan configurar las credenciales del canal y validar los renders reales. Ningún flujo tiene programación automática. Todas las subidas están bloqueadas salvo activación manual explícita y son PRIVADAS.

## Arquitectura

| Archivo | Función |
|---|---|
| preparar_contenido.py | Borradores editoriales anteriores |
| temas_verificados.json | Fuentes y afirmaciones oficiales |
| editorial.py | Elige temas vigentes, evita duplicados y prepara guiones |
| descubrir_noticias.py | Candidatos de PlayStation Blog y Xbox Wire, nunca autoconfirmados |
| generar_short.py | Gráficos originales de tarjetas |
| motor_video.py | Voz Piper por escena, MP4 9:16 y 16:9, miniaturas |
| control_calidad.py | Comprueba vídeo, audio, resolución y fuentes |
| autorizar_youtube_local.py | Genera la credencial OAuth con consentimiento local |
| subir_youtube_privado.py | Verifica el canal y sube solamente como privado |
| registrar_subida.py | Guarda historial tras confirmación de privacidad |
| historial_publicados.json | Evita subir repetidamente el mismo tema |

## GitHub Actions

1. **Píxel Feroz - Produccion completa (Short / Largo)**: flujo manual para elegir tema, narrar, renderizar, revisar calidad y crear archivos descargables. Si marcas subir_privado y escribes literalmente SUBIR_PRIVADO, intentará subir como PRIVADO al canal autorizado. Por defecto no sube nada.
2. **Píxel Feroz - Descubrir noticias (sin publicar)**: recopila enlaces de fuentes oficiales. Solo entrega propuestas sin convertirlas en temas confirmados.
3. **Píxel Feroz - Borrador manual**: flujo editorial anterior, también manual.

No hay ningún cron ni publicación pública. El código de los canales Dato Nebular y Alerta Binaria no ha sido modificado.

## Configuración del canal de YouTube (pendiente)

1. Crear o identificar el canal independiente Píxel Feroz y obtener el ID exacto en YouTube Studio → Configuración → Canal → Configuración avanzada.
2. Crear un proyecto de Google Cloud para Píxel Feroz, activar **YouTube Data API v3**, configurar el consentimiento OAuth y crear un cliente OAuth **Desktop**. Descargar su archivo de cliente al ordenador; no subirlo a GitHub.
3. En el ordenador, con Python instalado y una copia local del repositorio, instalar dependencias con el comando: python -m pip install -r requirements.txt
4. Autorizar el canal con: python autorizar_youtube_local.py --client-secrets RUTA_DEL_CLIENTE_OAUTH.json
5. Copiar LOCALMENTE el contenido íntegro del archivo youtube_oauth_privado.json a GitHub → Settings → Secrets and variables → Actions → secret **YOUTUBE_OAUTH_JSON**. Nunca compartir ni subir el archivo.
6. El ID público de Píxel Feroz está guardado en `config.json` (`UCgT82gfTjIw2o-CtmQgSS3w`). No es necesario crear un secreto para este identificador. El sistema compara la identidad OAuth contra ese ID antes de subir.
7. Primero generar y revisar vídeo con subir_privado=false. Después, si se ha comprobado calidad y fuentes, ejecutar el flujo manual con subir_privado=true y confirmacion=SUBIR_PRIVADO. En YouTube quedará **privado** para revisión final.

Los proyectos de YouTube API no verificados pueden estar limitados a subidas privadas. Un OAuth en modo Testing puede necesitar renovación del consentimiento. Consultar políticas actuales de Google Cloud.

## Guiones y temas

Cada objeto de temas_verificados.json exige:
- id único (minúsculas, números, guion o guion bajo)
- titulo, gancho, contexto, estado="confirmado"
- fecha_verificacion ISO (YYYY-MM-DD)
- hechos: lista de al menos 2 elementos, cada uno con texto y fuente oficial HTTPS
- opcionales: prioridad y vigente_hasta (fecha tras la cual el tema no se elige)

Para **vídeos largos** añadir:
- guion_largo: texto aprobado de al menos 650 palabras
- escenas_largas: al menos ocho párrafos definitivos, con 20 palabras o más cada uno, sumando al menos 650 palabras. La narración usa estas escenas.

La IA no inventa hechos ni rellena documentales largos. Si no quedan temas verificados, se interrumpe la producción y hay que añadir nuevos. Para las novedades detectadas, revisar manualmente fuentes y datos antes de confirmar un tema.

## Ejecutar localmente (cuando se decida iniciar las comprobaciones)

Instalar FFmpeg/ffprobe y las fuentes DejaVu. Después:
- python -m pip install -r requirements.txt
- python -m unittest discover -s . -p "test_*.py"
- python editorial.py --formato short
- python motor_video.py
- python control_calidad.py --formato short

La primera producción descargará un modelo Piper de voz española. Los MP4, planes, descripciones y miniaturas se crean en salida/. No se han generado vídeos durante esta fase de preparación.

## Seguridad y limitaciones

- Todas las subidas del proyecto son PRIVADAS y exigen una confirmación manual explícita; no hay autopublicación pública.
- El render utiliza gráficos originales basados en texto; no se copian clips ni capturas de otros canales. No afirmar que el contenido es monetizable sin evaluar originalidad y políticas de YouTube.
- La comprobación de enlaces HTTPS y dominios autorizados **no** acredita que cada afirmación esté respaldada por la página: revisión humana obligatoria.
- Antes de repetir una subida fallida, consultar YouTube Studio. Si YouTube recibió un vídeo y falló el registro posterior, una repetición podría duplicarlo.
- Los repositorios privados comparten los minutos de GitHub Actions de la cuenta. Separar repositorios NO separa esa cuota. No hay ejecución programada.
- Los nuevos módulos (render/audio/YouTube) están escritos pero todavía NO ejecutados ni validados; faltan pruebas de extremo a extremo y configurar OAuth.

## Fuente principal

Rockstar Games: https://www.rockstargames.com/VI
