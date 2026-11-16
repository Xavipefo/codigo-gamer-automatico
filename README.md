# Píxel Feroz — sistema independiente de YouTube

**Estado actual:** conexión OAuth de Píxel Feroz verificada en GitHub Actions (16-11-2026). Los módulos de producción y subida privada están implementados y revisados estáticamente, pero **el renderizador y la subida real todavía no se han probado de extremo a extremo**. No hay ejecuciones programadas ni publicaciones públicas automáticas.

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

## Configuración del canal de YouTube (OAuth ya configurado)

1. Crear o identificar el canal independiente Píxel Feroz y obtener el ID exacto en YouTube Studio → Configuración → Canal → Configuración avanzada.
2. Crear un proyecto de Google Cloud para Píxel Feroz, activar **YouTube Data API v3**, configurar el consentimiento OAuth y crear un cliente OAuth **Desktop**. Descargar su archivo de cliente al ordenador; no subirlo a GitHub.
3. En el ordenador, con Python instalado y una copia local del repositorio, instalar dependencias con el comando: python -m pip install -r requirements.txt
4. Autorizar el canal con: python autorizar_youtube_local.py --client-secrets RUTA_DEL_CLIENTE_OAUTH.json
5. Copiar LOCALMENTE el contenido íntegro del archivo youtube_oauth_privado.json a GitHub → Settings → Secrets and variables → Actions → secret **YOUTUBE_OAUTH_JSON**. Nunca compartir ni subir el archivo.
6. El ID público de Píxel Feroz está guardado en `config.json` (`UCgT82gfTjIw2o-CtmQgSS3w`). No es necesario crear un secreto para este identificador. El sistema compara la identidad OAuth contra ese ID antes de subir.
7. La comprobación `Pixel Feroz - Verificar conexion YouTube` terminó correctamente el 16-11-2026: el token corresponde al ID declarado. Las credenciales ya están guardadas en GitHub Secrets. Primero generar y revisar vídeo con subir_privado=false. Después, si se ha comprobado calidad y fuentes, ejecutar el flujo manual con subir_privado=true y confirmacion=SUBIR_PRIVADO. En YouTube quedará **privado** para revisión final.

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

## Repositorio público y primeros vídeos

La publicación del código en GitHub es distinta de la publicación de vídeos en YouTube:

- GitHub Actions ofrece ejecuciones gratuitas en runners estándar de repositorios públicos, pero **el almacenamiento de artifacts y otros recursos puede seguir teniendo límites**.
- **Los logs y artifacts de un repositorio público son accesibles públicamente**. Por eso `produccion_completa.yml` solo adjunta MP4 en repositorios privados. En un repositorio público, el workflow exige `subir_privado=true` y la confirmación `SUBIR_PRIVADO`, y deja el vídeo en YouTube Studio como **privado**. No se publica automáticamente.
- El OAuth del canal está en GitHub Secrets y su contenido no forma parte del código. Antes de hacer público un repositorio, revisar los archivos y el historial de commits: la protección de secretos no hace privado al resto del contenido.
- Ya hay cuatro temas en `temas_verificados.json`, incluidos dos Shorts nuevos sobre precarga y rendimiento. Las escaletas están en `contenido/primeros_videos.md`.
- Para la primera producción, recomendamos el tema `gta6-precarga-212gb` antes del 19 de noviembre de 2026. Las fichas basadas en noticias anteriores al estreno tienen fecha de caducidad para evitar publicar información desactualizada.

**Advertencia:** aún no se ha generado un MP4 con este motor. La primera ejecución es una producción piloto y puede requerir corregir errores técnicos. Si falla después de enviar contenido a YouTube, comprobar YouTube Studio antes de repetir la ejecución, para evitar duplicados.

## Revisión técnica del 16-11-2026

- `motor_video.py`: el audio y la imagen de cada escena se montan juntos en un fragmento MP4, con un breve silencio final; después se concatenan fragmentos homogéneos. Evita la estimación imprecisa de duraciones por número de palabras.
- `control_calidad.py`: comprueba pistas H264/AAC, resolución, diferencias de duración audio-vídeo, miniatura JPEG, datos editoriales y huella SHA-256 del guion.
- `subir_youtube_privado.py`: antes de `videos.insert`, revisa la lista de subidas del propio canal buscando `PF-ID`; falla de forma segura si no puede comprobar los duplicados. Tras insertar, escribe inmediatamente el ID y verifica privacidad privada con reintentos.
- `preparar_contenido.py`: ya no se rompe si hay temas históricos caducados y quedan otros vigentes.
- `generar_short.py` y el workflow de producción: reutilizan el archivo pequeño de configuración de Piper y el modelo de voz por caché de GitHub Actions, guardándola antes de subir.
- `test_subida_segura.py` y los test editoriales incluyen comprobaciones de regresión con respuestas de YouTube simuladas. **Añadidos al repositorio, sin ejecutar durante esta revisión.**

**Importante:** la búsqueda de duplicados recorre hasta 600 vídeos recientes. Si el canal supera ese límite o YouTube no responde, la subida se bloquea para revisión manual. Ningún sistema elimina por completo los duplicados tras un fallo de red no confirmado.

La voz y las tarjetas son un primer motor audiovisual; su calidad estética y su potencial de monetización se deben evaluar antes de publicar material público. El sistema **no inventa nuevos hechos ni guiones largos automáticamente**: exige temas confirmados por un editor.

## Seguridad y limitaciones

- Todas las subidas del proyecto son PRIVADAS y exigen una confirmación manual explícita; no hay autopublicación pública.
- El render utiliza gráficos originales basados en texto; no se copian clips ni capturas de otros canales. No afirmar que el contenido es monetizable sin evaluar originalidad y políticas de YouTube.
- La comprobación de enlaces HTTPS y dominios autorizados **no** acredita que cada afirmación esté respaldada por la página: revisión humana obligatoria.
- Antes de repetir una subida fallida, consultar YouTube Studio. Si YouTube recibió un vídeo y falló el registro posterior, una repetición podría duplicarlo.
- Los repositorios privados comparten los minutos de GitHub Actions de la cuenta. Separar repositorios NO separa esa cuota. No hay ejecución programada.
- OAuth ya está validado. Los nuevos módulos (render/audio/subida de MP4) están escritos pero todavía NO ejecutados ni validados de extremo a extremo; falta revisar los MP4 y la primera subida privada.

## Fuente principal

Rockstar Games: https://www.rockstargames.com/VI
