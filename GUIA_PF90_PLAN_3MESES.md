# PF-92 — Plan editorial de 3 meses para Píxel Feroz

**Periodo:** 24 de noviembre de 2026 a 23 de febrero de 2027, hora Europe/Madrid. **Tema principal actual:** GTA VI, con estructura para ampliar Píxel Feroz a otros videojuegos en el futuro.

## Producción semanal y formatos
- **Short de historia diario:** 14:30. Serie `Historia de GTA VI`, episodios numerados de 001 a 092, cronología de misiones. Aviso de spoilers a partir del episodio 002.
- **Shorts de actualidad/descubrimientos:** 19:00 y 23:30 todos los días.
- **Short extra:** 17:00 los viernes y sábados.
- **Documentales:** lunes, miércoles, viernes y domingo a las 21:00.
- **Total 92 días:** 92 Shorts de historia + 210 Shorts generales = **302 Shorts**, y **52 documentales**. El calendario NO publica automáticamente; primero se genera y revisa en privado.

## Próximo documental prioritario
**ID:** `gta6-vs-gtav-comparativa-profunda-20261124`
**Tema:** GTA VI vs GTA V: la comparativa definitiva de Rockstar.
Está primero en `colas/documentales.json` y en el primer hueco largo del calendario. Incluye 24 bloques narrativos (más de 2.400 palabras), 12 hechos referenciados, más de 20 perspectivas de comparación, tres propuestas de título y tres propuestas de portada. La duración prevista es de aproximadamente 15 a 25 minutos. Se debe contrastar con gameplay real toda valoración de conducción, físicas, inteligencia artificial o rendimiento; no afirmar superioridad sin prueba. Ningún workflow lo ha publicado por el mero hecho de añadirlo a la cola.

## Dónde están los temas
- `colas/calendario_3meses.json`: las 354 posiciones con su fecha, hora, ID, formato, tema y estado.
- `series/historia_gtavi_92_dias.json`: 92 episodios de historia, ordenados por jornadas y capítulos con fuentes y necesidades de prueba.
- `colas/historia_shorts.json`: la cola operativa de **episodios realmente confirmados**.
- `colas/shorts.json`: Shorts generales confirmados, en el orden real de generación.
- `colas/programa_shorts_generales_210.json`: planificación curada de 210 posiciones generalistas, con 66 focos diferentes.
- `colas/documentales.json`: próximos documentales confirmados; comienza con GTA VI vs GTA V.
- `colas/programa_documentales_50.json`: las otras 50 ideas documentales, cada una con foco diferente y esquema editorial propio.
- `colas/ideas_shorts_3meses.json` y `colas/ideas_documentales_3meses.json`: repositorios amplios de ideas de reserva.

## Protección de la veracidad y los spoilers
La historia del juego es reciente y distintas guías **no coinciden necesariamente** en el número exacto de misiones, su orden ni sus objetivos. Por ello los nombres de la serie son **planificación**, no afirmaciones sobre sucesos ya verificados. Las ideas marcadas `pendiente_verificacion_gameplay` **NO se pueden generar automáticamente** hasta disponer de fuentes contrastadas y material de juego propio o autorizado. El primer episodio, con antecedentes oficiales de Jason y Lucia, sí está en la cola confirmada. Para episodios de misiones posteriores se deben comprobar narración, escenas y derechos sobre el material; no mostrar giros o finales antes del aviso.

Rockstar proporciona un resumen y biografías oficiales en:
- https://www.rockstargames.com/VI
- https://www.rockstargames.com/VI/only-in-leonida
- https://www.rockstargames.com/VI/music
- https://www.rockstargames.com/newswire/article/39akk424a9oo53/grand-theft-auto-vi-now-available

Guías de misiones utilizadas para planificar la secuencia, **que requieren verificación**:
- https://www.powerpyx.com/gta-6-full-walkthrough-all-missions/
- https://www.pcgamer.com/games/grand-theft-auto/gta-6-mission-list/

## Cómo generar los dos tipos de Shorts
- Workflow [Crear Short privado](.github/workflows/crear_short_privado.yml): elegir línea editorial `general` o `historia`, dejar ID vacío para el siguiente.
- Workflow [Short diario HISTORIA GTA VI](.github/workflows/crear_short_historia_privado.yml): solo el siguiente episodio aprobado en la subcola historia.
- [Crear vídeo largo privado](.github/workflows/crear_largo_privado.yml): dejar ID vacío para empezar por `gta6-vs-gtav-comparativa-profunda-20261124`.
- El avance de cualquiera de las colas requiere que se confirme una subida `private`. El error en montaje, audio o YouTube no consume el tema; la historia no afecta a documentales ni a Shorts generales.

## Qué está confirmado y qué está planificado
La cifra de 354 posiciones **no equivale a 354 producciones listas**. Los temas verificados y disponibles deben comprobarse en las tres colas operativas, no en los ficheros de ideas. La generación de tres meses sin interrupciones requiere seguir investigando misiones y nuevo contenido, así como asegurarse de disponer de clips o imágenes autorizados, sin inflar con formatos repetitivos.

## Calidad y monetización
Evitar vídeos que repitan literalmente el mismo hecho. Cada Short necesita tesis, gancho y recursos únicos. Los documentales necesitan varias evidencias, narración sustancial y montaje que corresponda al guion. Todas las subidas automáticas son únicamente **privadas**; programación pública manual tras revisión visual y narrativa. No reproducir bandas sonoras protegidas en las pruebas.
