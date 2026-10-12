# Fuentes de datos

## Overture Maps Buildings

- Rol: geometría consolidada principal de edificios.
- Acceso: cliente Python oficial y consulta por bounding box; el catálogo STAC selecciona el release vigente.
- Campos usados: GERS `id`, geometría, versión, fuentes, altura, pisos, subtipo, clase y propiedades de fachada/techo disponibles.
- Licencia del tema Buildings: ODbL.
- Precaución: Overture ya integra OSM, Microsoft Global ML Building Footprints y Google Open Buildings, entre otras fuentes. City3D no vuelve a descargar esos conjuntos por defecto.

## OpenStreetMap

- Rol: carreteras, geometría alternativa y enriquecimiento de atributos.
- Acceso MVP: Overpass para radios de hasta 1 km; se envía User-Agent y no se ejecutan consultas paralelas. Si las instancias fallan, se usa la OSM Map API para ese mismo bounding box pequeño y se reconstruyen las geometrías desde nodos/vías.
- Para regiones mayores: descargar PBF regional y procesar localmente; no ampliar indiscriminadamente los límites de Overpass.
- Licencia: ODbL; atribución obligatoria.

## OSM2World

- Estado: investigado, no instalado, adaptador pendiente.
- Capacidades vigentes observadas: aplicación de escritorio/CLI/biblioteca; exporta glTF, GLB, OBJ y POV; admite PBR y LOD.
- Regla: al instalarlo se debe registrar la versión y verificar su `--help`; no se codifica una CLI supuesta.

## Relieve DEM — Mapzen Terrain Tiles / Terrarium

- Rol: elevación del terreno para la malla, base de edificios y superficie de vías.
- Acceso: teselas PNG Terrarium públicas en `elevation-tiles-prod`, zoom 12 por defecto.
- Codificación: `R × 256 + G + B / 256 − 32768`, resultado en metros.
- Cobertura: global compuesta por SRTM y otras fuentes abiertas; en Ecuador la cobertura global procede de SRTM.
- Resolución observada en Sangolquí: aproximadamente 38,22 m por píxel en zoom 12.
- Trazabilidad: se registra URL, zoom, teselas, cuadrícula, datum, cotas mínima/máxima, caché y fuentes de imagen cuando el servidor las informa.
- Limitación: no es un DSM de edificios ni reemplaza datos LiDAR/catastrales de mayor resolución.

## Fuentes pendientes

- DEM local GeoTIFF/Copernicus de mayor resolución: adaptadores futuros.
- ESA WorldCover: fase de ambientación, nunca como inventario de árboles.
- Microsoft/Google Open Buildings directos: solo si una prueba demuestra aporte adicional respecto al release Overture activo.
- GlobalBuildingAtlas: experimental; los subconjuntos CC BY-NC no se activarán en perfil comercial.
- Fuentes oficiales: requieren licencia y mecanismo de descarga verificados caso por caso; WMS no se tratará como vector.

## Política de fallo

Los proveedores se consultan secuencialmente para no abusar servicios públicos. Un fallo queda en los eventos y metadatos; el trabajo continúa si otra fuente produjo información válida. Si no hay datos, el sistema no inventa edificios.

# Fuentes añadidas en 0.4

- Copernicus GLO-30 Public (AWS, release 2021): DSM, metros, EGM2008, cobertura pública con huecos regionales. Lectura de ventanas COG; fallback Terrarium solo en modo automático.
- ESA WorldCover 2021 v200: clases de suelo, CC BY 4.0, muestreo categórico por vecino más cercano, sin árboles individuales.
- GeoJSON local WGS84: huellas y alturas/pisos con procedencia declarada, licencia validada contra lista admitida y hash del archivo.
- GeoTIFF local: DTM/DSM, CRS y datum vertical declarados, unidades m/ft, reproyección y comprobación de NoData.

Los adaptadores directos Microsoft/Google y las alturas raster TEMPO siguen pendientes. Consulte [detalle de fuentes y límites](precision-workflow.md).

