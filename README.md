# Píxel Feroz — automatización de vídeos de videojuegos

**Actualizado:** 18 de noviembre de 2026. Sistema independiente del canal Dato Nebular.
Se generan **Shorts** y **vídeos largos** mediante acciones manuales de GitHub. Todas las subidas
a YouTube son **PRIVADAS** para revisión. Ninguna acción publica automáticamente al público.

## Estreno de GTA VI — jueves 19 de noviembre

**[Guía operativa y tabla de IDs para producir hoy](GUIA_ESTRENO_19_NOVIEMBRE.md)**

El Short de las 00:05 tiene preparada una ejecución cron **solo privada**
para el 18/11 a las 20:37 CET. La publicación pública sigue siendo manual;
no asumir que GitHub garantiza la hora de su ejecución.


Se han añadido cinco temas nuevos de Shorts para **00:05, 09:00, 12:30,
16:30 y 20:00** y un largo para **22:00** (hora de Madrid). Las horas
son propuestas de publicación MANUAL, nunca publicación automática.
Consultar `calendario_publicacion.json` y los primeros seis registros de
`temas_verificados.json`. El Short de medianoche puede generarse en
PRIVADO antes del estreno; publicarlo solo después de las 00:00 locales.

Los Shorts usan imágenes de Rockstar con variedad por escena. Los largos
comparten esas imágenes, cambian de plano cada ~7 s y pueden intercalar
clips oficiales breves cuando esté disponible el ZIP de Rockstar.
Ambos exportan un mosaico y fotos a GitHub Actions (Artifacts), sin
guardar MP4 inéditos ni secretos en un repositorio público.

## Situación del canal

- Canal autorizado mediante OAuth: `UCgT82gfTjIw2o-CtmQgSS3w`.
- Gemini para guiones validado. Shorts anteriores subidos en privado y miniaturas confirmadas.
- **Voz principal aprobada: Ryan (Qwen3-TTS 0.6B libre)** para Shorts y largos.
  Un Short de 37,75 segundos fue generado, validado y subido en PRIVADO
  ([ver ejecución](https://github.com/Xavipefo/codigo-gamer-automatico/actions/runs/44070297476)).
  La voz se revisó manualmente y quedó aprobada. Aiden está descartada.
- **Pendiente de prueba de extremo a extremo: vídeo largo con Ryan**.
  Este formato puede requerir hasta varias horas de CPU, sin garantía
  de completar en el límite de ejecución de GitHub.
- Clips de videojuegos: el motor admite material propio/autorizado; **no existe ningún
  clip de GTA configurado todavía**. En su ausencia utiliza gráficos originales animados.

## Lanzamiento GTA VI — preparación 18–22 de noviembre de 2026

**[Guía de lanzamiento, programación, derechos y producción](GUIA_LANZAMIENTO_GTA_VI.md)**

- [0. Preparar cola y tres portadas](.github/workflows/preparar_cola_gta6.yml):
  borradores y calendario público descargable, **sin generar MP4 ni subir**.
- [3. Producir lote de 1–5 Shorts PRIVADOS con Ryan](.github/workflows/lote_shorts_privados.yml):
  acción manual, una instalación de modelos por lote, controla duplicados
  y registra cada ID privado antes del siguiente vídeo.
- [Calendario con 21 franjas](calendario_publicacion.json):
  13 Shorts y 5 largos entre jueves 19 y domingo 22, más 3 franjas miércoles.
- [Ideas postlanzamiento por verificar](ideas_postlanzamiento.json):
  nunca producir como hechos sin evidencia reciente.

Los workflows de producción NO publican al público ni activan
la prueba A/B de YouTube, que se hace después desde Studio.

## Botones que se usan en GitHub Actions

| Acción | Para qué sirve | Resultado |
|---|---|---|
| [1. Crear Short privado](.github/workflows/crear_short_privado.yml) | Siguiente noticia pendiente | YouTube **privado** |
| [2. Crear vídeo largo privado](.github/workflows/crear_largo_privado.yml) | Siguiente tema largo pendiente | YouTube **privado** |
| [Probar acento de España (Gemini)](.github/workflows/probar_voz_castellana.yml) | Dos audios de ejemplo Achird/Charon | Artifact WAV, nunca YouTube |
| [Verificar Gemini](.github/workflows/verificar_gemini.yml) | Verificar clave/modelo para guiones | Ningún vídeo |
| [Reparar miniatura privada](.github/workflows/reparar_miniatura.yml) | Aplicar miniatura a un vídeo privado existente | No vuelve a subir el vídeo |
| [Validar código](.github/workflows/validar_codigo.yml) | Pruebas Python | No sube vídeos |
| [Descubrir noticias](.github/workflows/descubrir_noticias.yml) | Candidatos de fuentes oficiales | Artifact editorial |

Los botones de Shorts y largos tienen un campo opcional **tema**: en blanco significa
*el primer tema vigente y todavía no subido del formato solicitado*. La cola está en
`temas_verificados.json` y **respeta estrictamente su orden físico**. Los vídeos
subidos quedan registrados en `historial_publicados.json` con claves
`(tema_id, formato)`, evitando duplicados de cada modalidad. La comprobación remota
en YouTube es una segunda barrera.

**Nunca pulses repetidamente Run workflow si hubo un error después de subir**:
comprueba primero YouTube Studio y el historial, o podrías crear duplicados.

## Narradores y voz

`config.json` contiene:

```json
"motor_voz": "qwen3-tts-0.6b",
"voz_qwen_principal": "Ryan",
"voces_por_formato": {
  "short": "Achird",
  "largo": "Charon"
}
```

`editorial.py` asigna **Ryan** al plan del vídeo al elegir Qwen
(predeterminado). `voz_qwen_produccion.py` descarga pesos libres oficiales,
los carga una vez por vídeo y genera los WAV en CPU, sin APIs TTS.
`motor_video.py` monta cada fragmento de audio y vídeo sincronizado.

- Ryan: voz de presentador aprobada por el usuario en Short de producción.
- Aiden: descartado.
- Achird y Charon: voces históricas de Gemini, disponibles solo si se
  selecciona explícitamente el motor antiguo en el workflow.
- Los guiones con IA **siguen usando Gemini solo para TEXTO**;
  las limitaciones de su API para guiones siguen vigentes.
- Si falla la voz, el vídeo **se detiene antes de subir**.
- Los vídeos largos muestran rótulos abreviados, sin modificar el guion.

**Coste de TTS:** 0 € de API y sin Azure. Los ejecutores CPU de repositorios
públicos están sujetos a las reglas y límites de GitHub. La calidad de
los largos aún no está verificada.

Los prototipos anteriores de Piper/Kokoro siguen como scripts históricos de
prueba, **no como motor de producción**.

## Banco oficial GTA VI y paquetes visuales para revisión (18/11/2026)

**Shorts privados:** el pipeline descarga automáticamente el archivo de
capturas oficiales de Rockstar desde
https://www.rockstargames.com/VI/media/screenshots y utiliza estas
fotografías en casi todas las escenas. No vuelve a producir Shorts
compuestos únicamente de tarjetas: si el ZIP o las fotos no se pueden
validar, se corta la producción **antes de cargar Qwen Ryan y antes de subir**.
Los materiales se almacenan en `.cache/rockstar/`, excluida de Git,
y `actions/cache` evita repetir descargas entre ejecuciones si conserva
el archivo. No es una descarga directa desde YouTube.

El Short mantiene tarjetas solo como apoyo (normalmente cierre); usa
zoom/paneo sobre fotos reales, textos breves y prioridad de clips
autorizados si ya existiesen. La selección clasifica el nombre de las
imágenes (Lucia, Jason, Vice City, etc.) y busca coincidencias con el
tema narrado. Se incluye la atribución automáticamente en
`salida/descripcion.txt` **únicamente si el Short utiliza material de Rockstar**.

**Qué descargar de GitHub para analizar el resultado:**

- Desde *Píxel Feroz - 1. Crear Short privado* → apartado **Artifacts**:
  `pixel-feroz-imagenes-y-mosaico-<run_id>`. Contiene
  `mosaico_escenas.jpg`, capturas de las escenas, originales elegidos,
  `manifiesto_escenas.json` y un contacto del banco de Rockstar.
- Para preparar una biblioteca independiente sin producir vídeos:
  ejecutar manualmente *Píxel Feroz - Banco de imágenes oficiales GTA VI*.
  Su artifact contiene catálogo, mosaico y una selección de 36 fotos.
- Se retienen 14 días; no se guardan MP4 privados, audio ni guiones inéditos
  como artifacts de un repositorio público. El Short se sube **privado**.
- Si un artifact caduca, hay que generar otro desde Actions. Los recursos
  originales siguen accesibles desde la página oficial de Rockstar.

**Derechos y monetización:** que Rockstar permita descargar/compartir
material oficial NO garantiza autorización comercial. La política general
de Take-Two habla de tolerancia del uso no comercial y puede retirar
contenido. Añadir el crédito no sustituye obtener permiso ni la revisión
legal/editorial. Para monetizar o usarlo promocionalmente, consultar
directamente `copyright@take2games.com` y la política:
https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

## Nuevo estilo de Shorts: gaming-news (18 noviembre de 2026)

Los Shorts que no tengan material externo licenciado usan
`graficos_gaming.py`: retícula técnica, acentos cian/rosa, módulos
de información, titulares grandes y cortes más frecuentes (hasta 18
palabras por segmento de voz). No aparecen las antiguas ilustraciones
urbanas generadas como fondo del Short. Son gráficos originales:
**NO se presentan como gameplay real ni como imágenes de GTA VI**.
Cuando existan fotos y clips válidamente licenciados se priorizan.

La voz Ryan, la revisión humana y las subidas estrictamente privadas
se mantienen. La prueba de integración completa con la nueva plantilla
debe revisarse antes de publicar al público.

## Visuales originales automáticos — sin archivos aportados por el usuario

Desde el 17/11/2026 se genera automáticamente un banco de **seis
ilustraciones editoriales originales por tema** mediante Pillow
(`visuales_originales.py`), sin descargar imágenes de Rockstar ni
necesitar `PF_IMAGENES_JSON`. Los fondos muestran paisajes urbanos
ficticios, carreteras y vehículos ilustrados: **no son capturas del
juego ni gameplay real**. El montaje utiliza zoom/paneo sobre cada
ilustración y rótulos breves. No son clips de juego.

- Si se configuran fotos con licencia válida, estas tienen preferencia.
- Si no se configuran fotos, se usan ilustraciones originales.
- Si se configuran clips autorizados, se intercalan con las imágenes.
- Los vídeos largos pueden generarse sin archivos externos. El botón
  `exigir_material_real` activa, opcionalmente, la comprobación estricta
  de un clip y una foto autorizados. Si no existen, bloquea la ejecución
  **antes** de cargar el modelo de voz.
- Se conserva subida **solo PRIVADA** y revisión humana antes de hacer
  público cualquier vídeo.

Se han localizado recursos oficiales para una futura biblioteca
de material sujeto a derechos:
https://www.rockstargames.com/VI/media/screenshots
https://www.rockstargames.com/VI/media/videos

Que los archivos sean descargables no implica permiso general de
reutilización comercial. No se importan automáticamente ni se declara
`derechos_confirmados` sin licencia verificable. Consultar:
https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

## Imágenes y clips de videojuegos — modo visual mejorado

El motor rota **hasta 6 clips** y **10 imágenes** por tema, con zoom
suave y rótulos discretos (hasta 11 palabras sobre imágenes/vídeo). Cuando
hay ambos recursos, prioriza aproximadamente 60 % de escenas con clips
y 40 % con fotos, salvo el cierre editorial. No interfiere con el
audio de Ryan (1.00x Shorts; **1.10x largos**).

Los nuevos **vídeos largos** tienen activada una comprobación de calidad:
cuando se marca `exigir_material_real`, antes de cargar Qwen o gastar minutos en narrar, comprueban que existe al
menos una imagen Y un clip autorizados del tema. Si faltan, muestran un
error útil y **no suben ningún vídeo**. Por defecto se utiliza el modo de ilustraciones originales, sin exigir archivos de terceros.

Configura los recursos con dos Secrets opcionales:
`PF_CLIPS_JSON` y `PF_IMAGENES_JSON`, en
**GitHub → Settings → Secrets and variables → Actions**.
Los vídeos **no se obtienen automáticamente** de YouTube o Rockstar.
Ejemplo de `PF_CLIPS_JSON` con **varios clips**:

```json
{
  "gta6-vice-city-leonida": [
    {
      "url": "https://tu-cdn.example/clip1.mp4",
      "derechos_confirmados": true,
      "origen": "propio",
      "credito": "Píxel Feroz",
      "fuente_publica": "https://tu-sitio.example/creditos"
    },
    {
      "url": "https://tu-cdn.example/clip2.mp4",
      "derechos_confirmados": true,
      "origen": "licenciado",
      "credito": "Titular de la licencia",
      "fuente_publica": "https://tu-sitio.example/licencia"
    }
  ]
}
```

Estos dominios son ilustrativos: sustituir por **URLs directas reales**
de archivos con derechos de uso comprobados. El manifiesto anterior
de un solo clip por tema sigue admitido por compatibilidad. Se usa
solo vídeo, se silencia su audio, se comprueba con FFprobe y se
registran los créditos en la descripción del vídeo.

Las imágenes usan una lista similar en `PF_IMAGENES_JSON` y aceptan
`origen` `propio`, `ia_original`, `licenciado`,
`oficial_autorizado`. Ver el ejemplo completo en
[GUIA_LANZAMIENTO_GTA_VI.md](GUIA_LANZAMIENTO_GTA_VI.md).
Ambos secretos deben ser privados; nunca almacenar sus archivos en
este repositorio público.

**Derechos:** una imagen publicada en Rockstar Newswire o un tráiler
descargable no son por sí solos una licencia de explotación comercial.
Rockstar dice que su política general de gameplay fan se dirige al
uso individual no comercial. Consultar la política actual y pedir permiso
si el canal se monetiza:
https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

## Guiones, fuentes y descripciones

- `temas_verificados.json` almacena cada tema y sus hechos con URLs oficiales
  y fecha de revisión. Solo se consideran los temas vigentes y confirmados.
- `generar_guion_ia.py` redacta desde esas fichas con
  `gemini-3.5-flash-lite`; el contenido puede tener errores y **debe revisarse**.
- `descripcion_general.txt` se añade al pie de la descripción específica,
  que incluye contexto, hechos, fuentes y hashtags, **sin códigos de control internos**.
- La protección contra duplicados utiliza `snippet.tags` (`pf_id_...` y
  `pf_formato_...`) más `historial_publicados.json`. El comprobador también
  reconoce los marcadores de las descripciones antiguas, sin añadirlos a
  ningún vídeo nuevo.
- `descubrir_noticias.yml` se ejecuta aproximadamente cada tres días y
  propone **candidatos**, sin convertirlos por sí solo en noticias confirmadas.
  No hay reposición 100 % autónoma de la cola validada.
- La fecha de estreno de GTA VI publicada por Rockstar, a fecha de esta
  revisión, es el **19 de noviembre de 2026**:
  https://www.rockstargames.com/VI

## Limpieza de descripciones de vídeos anteriores

La modificación de código afecta a **futuras subidas**, no cambia por sí
sola vídeos que ya están en YouTube. Los tres Shorts privados del
16/11/2026 conservan al final de sus descripciones las dos líneas antiguas
de control:

- `Identificador editorial: PF-ID:...`
- `Formato editorial: PF-FORMATO:short`

Si quieres retirarlas, entra en **YouTube Studio → Contenido → editar descripción**
de cada vídeo y elimina únicamente esas dos líneas; conserva las fuentes,
el título y el resto de la descripción. El historial de GitHub mantiene
el control principal de duplicados. El escaneo remoto de esos vídeos
antiguos deja de identificarlos después de quitar los marcadores salvo
que se añadan sus equivalentes a Etiquetas; no borrar
`historial_publicados.json`.

No automatizamos la edición de los vídeos anteriores porque el OAuth
actual solo tiene permiso de subida y lectura. `videos.update` requiere
una autorización nueva con `youtube` o `youtube.force-ssl`. No se han
solicitado permisos adicionales ni se ha modificado ningún vídeo existente.

## Seguridad del canal y del repositorio

Se necesitan estos secrets privados, ya configurados en este proyecto:

- `GEMINI_API_KEY`: guiones, no síntesis Qwen de producción.
- `YOUTUBE_OAUTH_JSON`: subir exclusivamente en privado al canal correcto.

Los secrets `PF_CLIPS_JSON` y `PF_IMAGENES_JSON` son opcionales, pero
el modo visual de largos exige al menos un recurso de cada tipo. No se
ha verificado que haya recursos cargados. Nunca mostrar los secretos en
conversaciones, archivos públicos ni logs.

`control_calidad.py` comprueba duración, codec H.264/AAC, dimensiones,
sincronización, miniatura, huella del guion, narrador previsto y referencias.
Un resultado técnico correcto **no sustituye** escuchar y ver el MP4.

Este repositorio es público. Por ello, el workflow no almacena MP4 privados
como artifacts públicos: los envía solamente a YouTube en modo privado.
La decisión de publicar desde YouTube Studio corresponde al propietario
después de revisar voz, imagen, copyright, títulos, descripción y contenido.
Los vídeos antiguos privados pueden conservar su voz anterior.

## Nueva elección de voz: Ryan (Qwen3-TTS 0.6B)

El usuario ha escuchado las muestras generadas con el modelo libre
(`run 44066820130`) y ha escogido **Ryan**, perfil `presentador`.
La voz Aiden, perfil `analista`, queda **descartada** por falta de
naturalidad. **No intentamos fingir dos narradores distintos**.

Se ha preparado una prueba del motor de producción usando Ryan tanto
para Shorts como para vídeos largos. El módulo `voz_qwen_produccion.py`
carga Qwen3-TTS **una sola vez por vídeo** y genera cada bloque en CPU
sin Azure ni Gemini TTS. Los guiones siguen usando Gemini (solo texto)
cuando el formato lo requiera. Se conserva el montaje con FFmpeg, los
controles técnicos y la subida **exclusivamente PRIVADA**.

### Primera prueba real recomendada (Short privado)

[Píxel Feroz - Probar Short privado con voz Ryan (Qwen libre)](
.github/workflows/crear_short_qwen_privado.yml)

Al ejecutarlo sobre `main` con `tema` vacío, el sistema elegirá el
siguiente Short verificado que aún no se haya subido, generará su guion
y narración con Ryan, montará vídeo y miniatura, validará los formatos y
solo entonces intentará subirlo en privado a YouTube. **No publica al público.**

**Ryan ya está seleccionado como voz predeterminada**, tanto en
`config.json` como en los botones habituales de Short y vídeo largo.
Los trabajos siguen subiendo únicamente a YouTube en privado; no existe
programación de publicación automática. **El vídeo largo está pendiente
de prueba real** y su duración de generación no está garantizada.

GitHub Actions ofrece CPU gratuita en repositorios públicos, sujeta
a sus condiciones y uso razonable. La prueba de dos muestras tardó
varios minutos. Los largos de 10–13 minutos podrían requerir mucho más
tiempo: no se promete todavía que completen dentro del timeout del
runner ni que igualen la entonación de la muestra.

## Opción prioritaria sin Azure: Qwen3-TTS libre en GitHub (17/11/2026)

Prueba de **síntesis de voz local y gratuita**, sin servicios de voz Gemini,
Azure ni tarjeta de crédito. La generación de **guiones** sigue usando su
configuración independiente (Gemini); Qwen sustituiría únicamente TTS.

- **Qwen3-TTS 0.6B CustomVoice**: menos memoria y descarga; voces masculinas
  predefinidas Ryan/Aiden. Español soportado, pero sus perfiles de origen son
  ingleses: **no podemos garantizar acento castellano peninsular**.
- **Qwen3-TTS 1.7B VoiceDesign**: permite describir una **voz original de
  España** con tono natural y estilo gamer, sin reproducir Achird o Charon.
  El checkpoint ocupa aproximadamente **4,5 GB** y puede ser muy lento en
  CPU. Solo activar si la prueba ligera no alcanza suficiente calidad.

**Workflow manual:**
[Píxel Feroz - Probar IA de voz LIBRE (Qwen3)](
.github/workflows/probar_voz_qwen_libre.yml)
1. `Actions > Píxel Feroz - Probar IA de voz LIBRE (Qwen3) > Run workflow`.
2. Primera prueba: `modelo=ligero`; después `modelo=diseno` si necesitamos
   más control de acento y la capacidad de GitHub lo permite.
3. El proceso descarga el checkpoint oficial Apache-2.0 en el runner CPU y
   genera dos archivos de ejemplo WAV, solo a partir de **texto de muestra
   público y original**. No lee vídeos privados ni secretos.
4. Si funciona, escuchar ambos archivos en el artifact
   `pixel-feroz-qwen-libre-<modelo>` (retención: 3 días).
5. **No hay cambio automático de narrador ni subida a YouTube** hasta
   escoger una voz y comprobar la calidad en español de España.

El repositorio es público, por lo que las muestras descargables también
pueden ser públicas: jamás incluir audio privado, materiales con derechos,
claves o guiones inéditos en este workflow. La caché solo guarda los pesos
públicos del modelo. Requiere un runner Ubuntu estándar con 4 CPU y 16 GB
RAM; la velocidad y consumo de disco están por validar y pueden forzar
una prueba fallida sin gastos de API.

Fuentes oficiales:
- https://github.com/QwenLM/Qwen3-TTS
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
- https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners

**No hace falta crear ni contratar una suscripción de Azure para esta prueba**.
Los scripts anteriores de Azure permanecen inactivos como alternativa.
La configuración de vídeos completos ya usa Ryan/Qwen3 como voz.
Gemini permanece solo para guiones y como alternativa TTS desactivada;
los vídeos seguirán subidos exclusivamente como privados.

## Alternativa gratuita a Gemini TTS: Azure Speech (16/11/2026)

El generador de **guiones** permanece en Gemini. La nueva alternativa
cambia **únicamente el motor de voz**. El nivel gratuito `F0` de
Azure AI Speech incluye 500.000 caracteres de TTS neuronal al mes
y hasta 20 transacciones/60 segundos, según Microsoft:
https://azure.microsoft.com/en-us/pricing/details/speech/
https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits

Se han implementado dos muestras originales de voces masculinas de España:

- **Álvaro** — `es-ES-AlvaroNeural`, candidato a narrar Shorts.
- **Arnau** — `es-ES-ArnauNeural`, candidato a reportajes largos.

**Es crucial escucharlas antes de sustituir a Achird y Charon.** Son voces
diferentes y aún no hay muestras reales de Azure generadas en el canal.
Hasta aprobación manual, la configuración de producción sigue en Gemini.

### Configuración de Azure sin publicar nada

1. Entrar en https://portal.azure.com/ y crear una suscripción si no existe.
2. Crear un recurso de **Speech (Voz)** con modalidad de precios **Free F0**,
   si está disponible; verificar que no se elige S0 ni otro recurso de pago.
3. En el recurso, abrir **Keys and Endpoint** para identificar la
   `KEY 1` y la **Region**. No publicar esa clave ni copiarla a README.
4. Ir a `Settings > Secrets and variables > Actions` de GitHub,
   crear los secrets `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION`.
   Ejemplo de región corta: `westeurope` (usar la real, no inventarla).
5. Ejecutar workflow **Píxel Feroz - Probar voces de España (Azure)**:
   https://github.com/Xavipefo/codigo-gamer-automatico/actions/workflows/probar_voces_azure.yml
   Produce solo dos WAV de texto de muestra original, descargables desde
   el artifact `pixel-feroz-azure-voces-es-ES`; no genera ni sube MP4.
6. Escuchar y elegir la mejor voz. **Solo entonces** cambiar
   `config.json -> motor_voz` a `azure-neural` para usar Azure en
   producción: Álvaro para Shorts y Arnau para largos. Los guiones seguirán
   generándose con Gemini hasta que se decida lo contrario.

Los secretos de Azure solo se usan dentro del proceso y no se incluyen
en archivos públicos ni logs. Para volver a Gemini basta con establecer
`motor_voz = gemini-3.8-flash-tts` en `config.json`.
En una cuenta nueva, Azure puede solicitar un medio de pago para
habilitar la suscripción: comprobar sus condiciones antes de registrarse.

## Recuperación de Gemini TTS y vídeos largos (16/11/2026)

**Incidencia real:** el workflow `43946742189` generó correctamente el
guion de 1.829 palabras y cinco audios con Charon; después recibió
`HTTP 429` repetidamente. La cuota de Google AI puede tener límites de
solicitudes por minuto, tokens por minuto o solicitudes por día, compartidos
por todo el proyecto. Un 429 **no demuestra por sí solo** qué límite
concreto se ha alcanzado. Los límites vigentes se consultan en
https://aistudio.google.com/rate-limit.

**Cambios ya integrados:**

- `motor_video.py` utiliza bloques equilibrados de hasta **100 palabras**,
  evitando solicitar audio innecesariamente en trozos de 50 palabras.
- `voz_produccion.py` deja un intervalo mínimo de **35 segundos entre
  peticiones TTS de un vídeo largo**, reduciendo ráfagas de solicitudes.
- `gemini_reintentos.py` respeta `Retry-After` y aplica pausas largas
  en HTTP 429. Identifica y corta la ejecución cuando el proveedor
  señala expresamente un límite **diario**, que no se soluciona esperando
  unos pocos minutos.
- El motor conserva localmente en el **runner temporal del trabajo actual**
  los WAV y clips MP4 ya válidos. Si Google vuelve a bloquear por minuto,
  el workflow reintenta **únicamente el paso de render** y recupera
  esos archivos, sin recrear el guion y sin duplicar la subida.
  El checkpoint se borra al completar el vídeo.
- Al tratarse de un **repositorio público**, no guardamos el guion ni
  los WAV inéditos como `GitHub Actions artifacts` públicos. En una
  ejecución nueva de GitHub empieza un runner nuevo: no hay continuidad
  entre runs. Esto es una medida de privacidad deliberada.
- El paso de subida a YouTube **nunca se reintenta automáticamente**.
  Todos los vídeos se envían exclusivamente como **privados** y
  quedan pendientes de revisión.

**Pruebas:** el workflow `validar_codigo.yml` instala FFmpeg y ejecuta
una prueba integral `test_render_integracion.py` que genera un MP4 real,
simula un fallo de cuota a mitad, comprueba la reutilización de WAV y MP4,
y termina el montaje. No realiza llamadas a Google ni sube vídeos.
Validación: https://github.com/Xavipefo/codigo-gamer-automatico/actions/runs/43949318365.

**Importante:** este resultado confirma el motor y su recuperación, no
la cuota real de la clave ni la calidad audible de un vídeo de 10-13
minutos. Si vuelve a aparecer `HTTP 429` por **RPD**, será necesario
esperar al reinicio de cuota según Google o aumentar la cuota del proyecto,
no repetir inmediatamente el workflow.

## Primer lanzamiento (revisión humana obligatoria)

1. Ejecutar **Crear Short privado** con el campo `tema` vacío.
2. Abrir el resultado en YouTube Studio y escuchar la voz **Achird**.
3. Revisar imágenes, pronunciación de GTA/PS5, precisión factual,
   miniatura, títulos y enlaces de la descripción.
4. Si la nueva versión es correcta, publicar manualmente ese vídeo.
5. Después, ejecutar **Crear vídeo largo privado** para probar **Charon**,
   revisar antes de decidir publicarlo.

**Si el workflow falla**, no lo repitas hasta conocer en qué paso terminó.
Si la subida privada ya se realizó, usa el vídeo existente y evita duplicados.

## Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `editorial.py` | Cola y asignación de narrador |
| `generar_guion_ia.py` | Guion factual con Gemini |
| `voz_produccion.py` | Reparto Achird/Charon, límites y TTS |
| `voz_gemini_castellano.py` | Solicitud REST de voz española y decodificación WAV |
| `motor_video.py` | Imágenes animadas, clips autorizados y MP4 |
| `video_material.py` | Carga opcional de clips confirmados |
| `control_calidad.py` | Comprobación técnica antes de subir |
| `subir_youtube_privado.py` | Subida PRIVADA y miniatura |
| `registrar_subida.py` | Registro de ID e historial |
