# Píxel Feroz — miniaturas de alto contraste para el viernes 20/11/2026

**Objetivo:** imagen oficial real de GTA VI como centro, pocas palabras (2–5), colores
neón saturados, texto legible en móvil y coherencia visual sin repetir portadas.
La fecha y las horas son de España peninsular (Europe/Madrid). Las franjas son
recomendaciones de publicación MANUAL, nunca publicaciones automáticas.

| Hora | Formato y tema | Titular A | Foto preferida del catálogo oficial | Dominante | Composición |
| --- | --- | --- | --- | --- | --- |
| **13:00** | Short: Raul Bautista, `gta6-raul-bautista` | **RAUL: EL ATRACADOR** | Primer plano oficial de **Raul**; alternativo escena oficial de Vice City | Amarillo eléctrico **#FFE730**, secundario coral **#FF4460** | Raul en zona superior, protagonista grande; degradado morado abajo, titular en blanco con contorno amarillo |
| **18:00** | Short: Boobie Ike, `gta6-boobie-ike` | **NEGOCIOS DE BOOBIE** | Captura oficial de **Boobie**; alternativo Vice City | Fucsia intenso **#FF2695**, secundario amarillo **#FFE237** | Boobie ocupa 65–70% del encuadre; titular abajo, neón rosa y barra amarilla |
| **21:00** | Short: Dre'Quan y Real Dimez, `gta6-drequan-real-dimez` | **REAL DIMEZ** | Imagen oficial de **Real Dimez**; alternativo **Dre'Quan** | Violeta brillante **#B154FF**, secundario cian **#00F8F5** | Dúo arriba, texto en el último tercio; contraste cian sobre fondo violeta |
| **22:00** | Largo: seis regiones de Leonida, `gta6-seis-regiones-leonida-20261120` | **6 ZONAS DE LEONIDA** | Panorámica oficial de **Vice City**; alternativos Cayos, Grassrivers y Port Gellhorn | Cian eléctrico **#00F7EF**, secundario rosa **#FF45A6** | Formato horizontal 1280×720: texto a la izquierda, paisaje oficial visible a la derecha y marco cian |

## Lenguaje visual común

- **Prioridad 1:** captura o artwork *real* descargado del catálogo oficial local de Rockstar, clasificado por tema; nunca capturas falsificadas de gameplay.
- **Prioridad 2:** personaje / paisaje grande; evitar collages con seis objetos pequeños. No colocar texto encima de caras.
- **Texto:** 2–5 palabras; tipografía negrita blanca con sombra negra y contorno de color muy saturado; legible en pantalla pequeña.
- **Composición:** Short 720×1280 con foto en el área superior y titular abajo; largo 1280×720 con foto preferentemente a la derecha y texto a la izquierda.
- **Marca:** etiqueta pequeña **PÍXEL FEROZ** arriba y **GTA VI** abajo. El protagonista debe ser el juego, no el logotipo.
- **Formato:** JPG optimizado de 2 MB como máximo. Versiones A/B/C para revisión manual en largos; no se activan experimentos automáticamente.
- **Fotos y derechos:** usar la galería pública de Rockstar (https://www.rockstargames.com/VI/media). Que se permita descargar una imagen no supone licencia comercial general; mantener revisión humana y atribución.
- **Nunca** automatizar la publicación pública. El pipeline genera y sube vídeos privados; después el propietario revisa y programa en YouTube Studio.

## Titulares alternativos para experimentos de los largos

1. **6 ZONAS DE LEONIDA** — cian, Vice City panorámica.
2. **VICE CITY Y MÁS** — fucsia, captura oficial de ciudad o paisaje.
3. **EL MUNDO DE GTA** — amarillo o violeta, imagen oficial de Leonida.

Los titulares deben reflejar los hechos oficiales; no hacer promesas de mecánicas, tamaño del mapa, trucos o secretos no verificados.

## Estado de automatización

El módulo `portadas_gta_neon.py` crea las portadas reales. `motor_video.py` lo usa para
`salida/miniatura.jpg` y `experimentos_portadas.py` para las tres variantes.
El banco de imágenes se prepara con `rockstar_media.py --preparar` y
`rockstar_extras.py --preparar`. Si no está disponible, no se inventa una imagen
del juego: se utiliza un fondo gráfico original, que deberá revisarse.

**Este plan y los cambios de código no implican que los MP4 del viernes estén ya generados.**
