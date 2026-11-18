# Píxel Feroz — lanzamiento de GTA VI (17–22 noviembre de 2026)

**Actualización de 18/11/2026:** la guía operativa vigente y el orden de
producción están en [GUIA_ESTRENO_19_NOVIEMBRE.md](GUIA_ESTRENO_19_NOVIEMBRE.md).
Los horarios anteriores de esta guía son históricos: el 19/11 hay Short extra
a las **00:05**, cuatro Shorts a lo largo del día y un largo a las **22:00**.
Los largos ya tienen capturas oficiales y montaje con subplanos; clips
oficiales opcionales. Publicación pública siempre MANUAL.


**Estado: infraestructura editorial preparada; NO equivale a 21 MP4 renderizados.**
El canal solo sube vídeos **privados**. Los horarios son objetivos de
PUBLICACIÓN MANUAL en YouTube Studio, no cronjobs de publicación pública.

## Horarios (Europe/Madrid)
Rockstar anuncia GTA VI para jueves 19/11/2026, medianoche local:
https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s?pubDate=20261110

- Normal: Shorts 13:00 y 18:00. Largos lunes, miércoles, viernes, domingo 21:00.
- Miércoles 18: Shorts 13:00 y 18:00; largo 21:00.
- Jueves 19: Shorts 10:30, 13:00, 17:30 y 19:30; largos 15:00 y 22:00.
- Viernes 20, sábado 21, domingo 22: Shorts 13:00, 18:00 y 21:00; largo 22:00.

En total: 21 franjas del 18 al 22, de las que 13 Shorts y 5 largos
pertenecen al especial del 19–22. Revisa **calendario_publicacion.json**.
Las horas son orientativas y NO activan ninguna publicación.

## Cola lista para trabajar en GitHub

Workflow: **Píxel Feroz - 0. Preparar cola y portadas GTA VI (sin subir)**.
Se activa manualmente o tras actualizar la cola editorial.
Genera un artifact para descargar:
- agenda.md, agenda.json y pendientes_verificacion.json
- borradores verificados con guion corto y descripción
- esquemas para largos pendientes de generación de guion IA
- tres portadas originales y tres títulos por largo como propuestas A/B

Los temas tienen afirmaciones y enlaces a Rockstar en
**temas_verificados.json**. Las ideas en **ideas_postlanzamiento.json**
NO incluyen afirmaciones sobre gameplay todavía desconocido; necesitan
verificación posterior (fuente oficial o grabación propia válida).
El repositorio y sus artifacts editoriales son públicos: NUNCA poner
en ellos secretos, gameplay inédito, imágenes privadas o MP4 sin publicar.

## Preparar vídeos completos

Usar los botones existentes **Crear Short privado** y **Crear vídeo
largo privado**. Indicar un ID de tema verificado o dejarlo vacío.
Todo se verifica antes de subir, y YouTube confirma estado privado.
El historial bloquea duplicados por tema y formato.

Voz Ryan (Qwen3-TTS): **1.00x Shorts / 1.10x largos**. El ritmo largo
se modifica con FFmpeg atempo sin alterar el tono. Este ajuste NO acelera
la inferencia de Qwen, que tardó cerca de 89 minutos por un largo de
12:06 en la prueba real. Los 5 largos especiales pueden requerir muchas
horas de CPU y 3 de ellos esperan material postlanzamiento verificable.

## Tres títulos + tres miniaturas

Cada largo nuevo genera un artifact de propuestas A/B de diseños
originales. **YouTube Studio debe iniciar el experimento manualmente
cuando el vídeo sea elegible y ya no esté privado.** No funciona
en Shorts ni en vídeos privados:
https://support.google.com/youtube/answer/16391400?hl=es

## Material oficial, arte IA, vídeos y permisos

- **PF_CLIPS_JSON**: admite ahora **hasta 6 clips cortos por tema**,
  descargados únicamente de enlaces HTTPS directos con permiso confirmado.
  El motor rota diferentes vídeos como fondo, descarta el audio original
  y superpone rótulos de hasta once palabras. Sin configurar, seguirá
  utilizando imágenes autorizadas o animaciones originales.
- **PF_IMAGENES_JSON**: admite ahora **hasta 10 imágenes por tema**
  (propias, IA original, licenciadas u oficiales con autorización).
  En el montaje se alternan con los clips; se usan fotos grandes,
  un zoom muy suave y rótulos discretos. El sistema añade los
  créditos de fotos y clips autorizados a la descripción.
- Cada elemento de PF_IMAGENES_JSON requiere URL de imagen directa
  HTTPS, derechos_confirmados=true, origen, credito y fuente_publica
  HTTPS. Orígenes: propio, ia_original, licenciado, oficial_autorizado.
  Ejemplo genérico de estructura (NO usar sin sustituir enlaces y
  comprobar realmente los permisos):

    {"gta6-vice-city-leonida":[{"url":"https://TU-CDN.example/foto.jpg",
    "derechos_confirmados":true,"origen":"ia_original",
    "credito":"Arte original Píxel Feroz",
    "fuente_publica":"https://TU-SITIO.example/creditos"}]}

### Formato real de PF_CLIPS_JSON (GitHub Secret)

El motor acepta una **lista** por tema (sustituye todos los dominios
de ejemplo por un almacenamiento del que tengas control de los derechos):

```json
{
  "gta6-vice-city-leonida": [
    {
      "url": "https://cdn.tu-dominio.example/clip-ciudad.mp4",
      "derechos_confirmados": true,
      "origen": "propio",
      "credito": "Píxel Feroz",
      "fuente_publica": "https://tu-dominio.example/creditos"
    },
    {
      "url": "https://cdn.tu-dominio.example/clip-ambiente.mp4",
      "derechos_confirmados": true,
      "origen": "licenciado",
      "credito": "Titular original de la licencia",
      "fuente_publica": "https://tu-dominio.example/licencia"
    }
  ]
}
```

Una sola entrada anterior en formato objeto también sigue siendo
aceptada por compatibilidad, pero las **entradas nuevas** deben tener
crédito, origen y enlace público de atribución. Máximo seis clips
de 2 a 180 segundos; se recomiendan piezas de 3–6 segundos.
No uses `urllib.request.urlretrieve` con URLs arbitrarias; el
descargador incluido valida HTTPS, destinos y limita tamaños,
rechaza redirecciones y verifica el vídeo con FFprobe.

**La alternancia automática no inventa ni busca clips de GTA VI.**
Hasta que se añadan URL legítimas a Secrets de GitHub, aparecerán
animaciones originales, no imágenes ni vídeo oficial. Citar la
fuente no concede autorización, especialmente para uso comercial.

- Fuentes de Rockstar para revisar permisos y catalogar recursos:
  https://www.rockstargames.com/VI/media
  https://www.rockstargames.com/VI/launch-gallery
  https://www.rockstargames.com/VI/only-in-leonida
  https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

**Citar la fuente NO concede licencia.** Rockstar limita determinados
usos comerciales, filtraciones, spoilers y escenas cinemáticas.
Antes de usar imágenes oficiales en un canal monetizable, verificar
permiso/licencia apropiados y evitar música protegida.

**Limitación pendiente:** el workflow admite arte/vídeo de IA que ya
se haya generado legítimamente, pero NO ejecuta aún un modelo IA
autónomo que cree nuevas imágenes o vídeos; un modelo pesado o un
proveedor adicional podría aumentar mucho el consumo o el coste.

## Prioridad inmediata

1. Descargar el artifact de agenda y borradores.
2. Generar en privado los temas confirmados uno por uno, empezando
   por Shorts y los largos que pueden hacerse antes del 19.
3. No fabricar novedades postlanzamiento: incorporar pruebas reales
   y después generar el guion/vídeo correspondiente.
4. Revisar cada vídeo y los tres títulos/portadas de cada largo.
5. Publicar manualmente en la franja elegida y lanzar A/B desde Studio
   cuando proceda. Evaluar audiencia real antes de ampliar volumen.
