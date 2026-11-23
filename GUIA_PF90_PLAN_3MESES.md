# PF-90 — Plan GTA VI, 24-11-2026 a 23-02-2027

**Shorts:** cada día 14:30, 19:00 y 23:30; extra 17:00 viernes y sábado. **Largos:** lunes/miércoles/viernes/domingo 21:00.

Las listas `colas/shorts.json` y `colas/documentales.json` contienen exclusivamente temas contrastados y disponibles. El primer tema apto se produce primero y se retira SOLO tras confirmar una subida PRIVADA a YouTube. Un error no consume el tema y un Short no excluye un documental independiente.

`colas/ideas_shorts_3meses.json` y `colas/ideas_documentales_3meses.json` son reserva de **propuestas no verificadas**, no guiones ni noticias confirmadas. `colas/calendario_3meses.json` distingue las posiciones confirmadas de las pendientes; no se deberán generar sin fuentes.

Para promocionar una idea se prepara una ficha JSON con `id, titulo, formato, gancho, contexto, hechos:[{texto,fuente},...], visuales_preferidos`; para un largo se añade `esquema_largo`. Tras revisar personalmente que cada fuente oficial respalda los hechos y que existen imágenes autorizadas: `python promocionar_idea_pf.py --ficha ficha.json --confirmacion FUENTES_REVISADAS`. El script la incorpora al catálogo y a la cola correspondiente, sin publicar.

El stock de ideas es suficiente en cantidad, pero el stock **confirmado** todavía no permite garantizar 302 Shorts y 52 largos. Hay que promocionar temas verificados periódicamente sin repetir enfoques ni fabricar noticias. La publicación final se programa manualmente en YouTube tras revisar narración, imágenes, títulos y miniatura.
