# Píxel Feroz — plan ejecutable del estreno de GTA VI (19/11/2026)

**Zona horaria:** Europe/Madrid (CET, España peninsular). **Estado:** temas verificados y agenda preparada; ninguna franja equivale a un vídeo público programado.

Rockstar confirma que GTA VI se desbloquea **a las 00:00 hora local del jueves 19 de noviembre** en PlayStation 5 y Xbox Series X|S:
https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s

## Calendario recomendado para publicar MANUALMENTE

| Fecha | Hora local | Formato | ID exacto para GitHub Actions | Título editorial |
|---|---|---|---|---|
| 19/11 | 00:05 | Short especial | `gta6-estreno-espana-0005` | GTA VI ya se estrena en España |
| 19/11 | 09:00 | Short | `gta6-estreno-tres-claves` | Tres claves oficiales del estreno |
| 19/11 | 12:30 | Short | `gta6-estreno-jason-lucia` | Jason y Lucia |
| 19/11 | 16:30 | Short | `gta6-estreno-zonas-leonida` | Lugares oficiales de Leonida |
| 19/11 | 20:00 | Short | `gta6-estreno-ediciones` | Standard, Ultimate y extras |
| 19/11 | 22:00 | Largo | `gta6-estreno-resumen-oficial-largo` | Todo lo confirmado oficialmente |

Las 00:05 son **después** del desbloqueo español, no «hoy a las doce del mediodía». Si todavía son las 23:xx del 18/11, NO publicar el Short titulado como si el estreno ya hubiera ocurrido.

**Preparación privada automática:** existe un workflow
[`estreno_medianoche_privado.yml`](.github/workflows/estreno_medianoche_privado.yml)
con disparo previsto el **18/11 a las 20:37 CET** (19:37 UTC). Solo
**genera y sube el Short en PRIVADO**, registra su ID y exige comprobación de
duplicados. El cron se protege por año y GitHub puede retrasar o perder
ejecuciones programadas. Revisa su estado en Actions; si no termina con
éxito, usa el botón manual con el ID exacto de arriba. **No se programa
ninguna publicación pública**: a las 00:05 el vídeo debe publicarse
manualmente desde YouTube Studio.


## Instrucciones de producción

1. En GitHub Actions ejecutar **Píxel Feroz - 0. Preparar cola y portadas GTA VI (sin subir)** para descargar la agenda y los borradores. Esta fase no crea MP4.
2. Para producir vídeos, usar **1. Crear Short privado** o **2. Crear vídeo largo privado** e indicar el **ID** de la tabla. Es preferible producir el Short de las 00:05 **antes** de medianoche, en modo privado.
3. Revisar el vídeo privado en YouTube Studio, así como el paquete de imágenes del artifact `pixel-feroz-<formato>-imagenes-y-mosaico-<run_id>`. No publicar un Short que afirme una novedad sin comprobarla.
4. Publicar **manualmente** en YouTube Studio en la hora objetivo. El script del repositorio **nunca publica de forma automática**, ni puede reservar por sí solo un estreno público.
5. Antes de generar varios Shorts usar `lote_shorts_privados.yml`, que conserva mosaicos separados por tema. Revisar el historial y no repetir una subida si ya se completó.

**Importante sobre el vídeo largo:** Qwen Ryan en CPU es costoso; una ejecución anterior necesitó aproximadamente 89 minutos para 12 minutos de vídeo. Generarlo de antemano y revisarlo; no planificar a última hora. La cadencia editorial no garantiza tiempos de render.

## Banco audiovisual oficial

El workflow descarga y verifica el ZIP de screenshots de
https://www.rockstargames.com/VI/media/screenshots
y añade, cuando estén accesibles, material de las secciones:
- Ultimate Edition Benefits
- Vintage Vice City Pack
- Artwork & Wallpapers
- Clips oficiales de GTA VI, desde https://www.rockstargames.com/VI/media/videos

`rockstar_media.py` clasifica capturas y evita repetir demasiadas imágenes seguidas del mismo personaje; `rockstar_extras.py` integra las imágenes complementarias cuando se pueden descargar; `rockstar_clips.py` valida los clips con FFprobe y los ofrece opcionalmente a los largos.

Los Shorts utilizan principalmente fotografías con texto breve. Los largos cambian de plano aproximadamente cada siete segundos, mezclando capturas y clips cuando el banco de vídeo está disponible, manteniendo **intacta** la voz de Ryan, sin reutilizar audio de los clips. Tanto Shorts como largos crean paquetes visuales descargables para analizar montaje, imágenes y créditos. La falta de clips no impide realizar un largo basado en capturas oficiales, pero se avisa del problema.

### Calidad y derechos

La página de Rockstar invita a descargar y compartir material, pero **citar en la descripción no constituye una licencia comercial**. Su política general permite en principio determinados usos **no comerciales** y se reserva la retirada del material. Los vídeos siguen **privados** hasta la revisión de derechos y contenido. Para monetización o usos promocionales, pedir autorización al titular:
https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material

Ni la galería ni los tráileres pueden utilizarse para presentar como real una característica no confirmada. No se incluyen filtraciones, bandas sonoras, cinemáticas aisladas ni supuestas impresiones de gameplay no comprobadas.

## Verificaciones automáticas

- `test_rockstar_media.py`: ZIP oficial, selección de capturas y fuentes.
- `test_montaje_rockstar.py`: mezcla técnica con fotos/clip de prueba y 20 FPS.
- `probar_rockstar_visual.yml`: smoke de Short y largo con capturas oficiales y audio de prueba, sin publicar.
- `planificar_lanzamiento.py`: valida la agenda y genera borradores basados en fuentes oficiales.

El archivo `calendario_publicacion.json` conserva el horario completo de 18 a 22 de noviembre. Los temas posteriores que exijan partidas reales o datos nuevos siguen pendientes hasta que existan evidencias verificables.
