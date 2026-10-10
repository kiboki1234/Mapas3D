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

## Fuentes pendientes

- DEM SRTM/Copernicus/local: fase de relieve.
- ESA WorldCover: fase de ambientación, nunca como inventario de árboles.
- Microsoft/Google Open Buildings directos: solo si una prueba demuestra aporte adicional respecto al release Overture activo.
- GlobalBuildingAtlas: experimental; los subconjuntos CC BY-NC no se activarán en perfil comercial.
- Fuentes oficiales: requieren licencia y mecanismo de descarga verificados caso por caso; WMS no se tratará como vector.

## Política de fallo

Los proveedores se consultan secuencialmente para no abusar servicios públicos. Un fallo queda en los eventos y metadatos; el trabajo continúa si otra fuente produjo información válida. Si no hay datos, el sistema no inventa edificios.

