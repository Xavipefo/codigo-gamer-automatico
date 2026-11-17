# Píxel Feroz — automatización de vídeos de videojuegos

**Actualizado:** 17 de noviembre de 2026. Sistema independiente del canal Dato Nebular.
Se generan **Shorts** y **vídeos largos** mediante acciones manuales de GitHub. Todas las subidas
a YouTube son **PRIVADAS** para revisión. Ninguna acción publica automáticamente al público.

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

## Imágenes, movimiento y clips de videojuegos

El motor crea tarjetas visuales originales y aplica movimiento de cámara suave.
Si cuentas con un vídeo propio o con autorización de uso explícita, puedes
facilitar un **enlace directo HTTPS a un MP4/MOV/WebM** mediante el secret opcional
`PF_CLIPS_JSON` en Settings → Secrets and variables → Actions:

```json
{
  "gta6-jason-lucia": {
    "url": "https://mi-servidor.example/videos/gta-autorizado.mp4",
    "derechos_confirmados": true
  }
}
```

El valor anterior es **solo un ejemplo**: ese enlace no existe y no se debe
copiar literalmente. El archivo ha de poder descargarse directamente sin
abrir una página web. Nunca incluir el enlace privado o material con derechos
limitados en el repositorio público. No se aceptan URLs de plataformas como
YouTube, Instagram, Rockstar o TikTok. El motor limita el tamaño a 120 MB,
comprueba que haya pista de vídeo y descarta el sonido original para mantener
la narración.

Tener acceso público a un tráiler/captura/gameplay **no equivale a permiso
para reutilizarlo comercialmente**. Verificar las condiciones de Rockstar,
Take-Two y del creador del archivo. No se insertan vídeos ajenos
automáticamente. El hecho de tener clips de juego no garantiza monetización:
la originalidad editorial y las normas de YouTube siguen siendo relevantes.

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

- `GEMINI_API_KEY`: guiones y síntesis de voz.
- `YOUTUBE_OAUTH_JSON`: subir exclusivamente en privado al canal correcto.

El secreto `PF_CLIPS_JSON` es opcional y actualmente no contiene clips
configurados. Nunca mostrar los secretos en conversaciones, archivos públicos
ni logs.

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
