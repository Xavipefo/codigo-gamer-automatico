# Píxel Feroz — PF-43, nuevos temas y lotes largos

## Contenido editorial

Se han preparado **9 Shorts y 2 vídeos largos** sobre regiones y personajes de GTA VI, todos con datos y enlaces a las fichas y galerías oficiales de Rockstar. Son análisis de material promocional, **no reseñas de gameplay grabado**. Están en `temas_verificados.json` y se producen solo en PRIVADO.

No publicar un vídeo solo porque una fuente pertenezca a Rockstar: revisar imágenes, afirmaciones, derechos y encaje con la narración. El banco visual descarga fotografías oficiales para revisión; la atribución no sustituye permisos comerciales.

## Nuevo botón de vídeos largos

En GitHub → Actions → **Píxel Feroz - 4. Producir lote de LARGOS PRIVADOS**:

1. Seleccionar entre 1 y 3 largos (no pedir más temas que los disponibles).
2. Opcional: indicar IDs exactos separados por `|`.
3. Elegir `GENERAR_PRIVADO` (por defecto `NO_EJECUTAR`).
4. Ejecutar el workflow y seguir cada vídeo en `crear_largo_privado.yml`.

El planificador reserva temas durante 72 horas en `reservas_largos.json`, evita duplicados del historial y despacha ejecuciones individuales en la cola existente. No genera múltiples MP4 en el mismo runner y **no los publica públicamente**. Si una ejecución falla después de subir, consultar YouTube Studio antes de repetirla.

## QC-01: control audiovisual real

Antes de subir cada Short o largo, se ejecuta `auditoria_audiovisual.py`:

- Comprueba vídeo y audio, duración y dimensiones.
- Analiza fotogramas separados a lo largo del MP4 y bloquea vídeos casi negros o congelados.
- Mide la presencia de audio en tres posiciones.
- Conserva un reporte JSON de la calidad técnica.

Los lotes de Shorts también pasan este control. QC-01 **NO** puede certificar que una fotografía represente exactamente el tema, que el guion sea correcto ni que haya licencia de monetización. Siempre se requiere revisión editorial humana.

## Pruebas

Ejecutar en un entorno con FFmpeg:

```bash
python -m unittest -v test_pf43_cola_oficial test_lote_largos_privados test_auditoria_audiovisual
```

No se realiza ninguna subida en estas pruebas.
