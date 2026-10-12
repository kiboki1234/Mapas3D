# Precisión geográfica — versión 0.5

## Qué puede hacer esta versión

El flujo une Overture y OSM, resuelve duplicados, permite priorizar huellas locales y genera GLB con relieve. Los proveedores globales cubren muchas regiones, pero no garantizan altura, actualidad o completitud en cada lugar. UTM se usa en latitudes habituales y UPS en regiones polares. Las regiones que atraviesan el antimeridiano o un polo deben dividirse; se rechazan con un mensaje explícito.

### Relieve

En **Modelo 3D → Fuente del relieve**:

- **Automático** intenta Copernicus GLO-30 Public (release AWS 2021) y, si falla, Terrarium. Se registra la sustitución y no se reutiliza el resultado parcial como modelo completo en el siguiente intento.
- **Copernicus** o **Terrarium** seleccionados explícitamente no se reemplazan silenciosamente.
- **GeoTIFF local** utiliza exclusivamente el archivo elegido. Un fallo local no provoca una sustitución por un DEM de menor detalle.

Copernicus es un **DSM**: puede contener árboles y tejados. No permite obtener automáticamente la altura de cada edificio, ni equivale a un DTM de terreno desnudo. Las elevaciones Copernicus se interpretan en metros sobre EGM2008. Terrarium depende de sus fuentes regionales. No se mezclan ni restan modelos con datums distintos.

Para apoyar edificios con altura sobre un DSM, City3D no toma el máximo de la huella como suelo: ajusta un plano local robusto con nodos vecinos situados fuera de las huellas de edificios. Así evita sumar la elevación del tejado dos veces. El método y el número de muestras quedan en el nodo GLB. En un DTM mantiene el ajuste directo a la superficie del terreno. Ninguno de los dos métodos sustituye una cota de implantación catastral o LiDAR.

La lectura usa ventanas limitadas (máximo 4 millones de píxeles) y peticiones parciales de GeoTIFF remotos. Se reproyecta la ventana a nodos de una cuadrícula de escena. NoData o cobertura incompleta producen un error; no se rellenan huecos con elevación cero. Los metadatos separan resolución nativa y separación de nodos: una malla más densa no implica mediciones más precisas.

### Cobertura del suelo

Active **WorldCover 2021** junto con el relieve. El adaptador consulta las teselas 3×3 grados v200, recorta la región y utiliza vecino más cercano, no interpolación entre códigos de clase. Cada triángulo toma la clase del nodo más cercano a su centro. Esta representación puede ser más gruesa que los píxeles originales de aproximadamente 10 m.

El GLB conserva materiales por clase y la leyenda en sus metadatos. Son colores temáticos, no colores reales observados ni fotografías. No se generan árboles individuales. Si WorldCover falla, se conserva el DEM y se muestra la advertencia.

## Importar datos de mayor detalle

Abra **Datos locales de mayor detalle**. Introduzca la fecha de los datos (no la fecha de descarga), nombre, autor/atribución y licencia documentada. City3D no certifica estas declaraciones ni convierte un archivo privado en datos abiertos.

Licencias admitidas en esta primera versión: CC0-1.0, CC-BY-4.0, ODbL-1.0 y CDLA-Permissive-2.0. Si el archivo tiene otros términos, no seleccione una licencia distinta para forzar su importación. Se requiere un adaptador/política específica.

### Edificios GeoJSON

- `FeatureCollection` RFC 7946, WGS84, polígonos 2D válidos (`Polygon` o `MultiPolygon`, patios admitidos).
- Máximo 10 MB, 20.000 elementos por archivo, cinco datasets por trabajo.
- `properties.height_m`: altura relativa al suelo, en metros; nunca una cota sobre el nivel del mar.
- `properties.num_floors`: número de pisos, si no hay altura explícita válida.
- `properties.height_estimated`: `true` para predicciones; no se etiquetarán como mediciones.
- `properties.name` e `id`: opcionales.

La importación no completa alturas desconocidas. En ausencia de datos conserva la huella. Las huellas locales tienen prioridad geométrica cuando se demuestra un duplicado; las alturas explícitas siguen teniendo prioridad sobre las estimadas, independientemente del proveedor. Se conservan conflictos, fuentes por atributo y SHA-256 del archivo.

### Elevación GeoTIFF

- Una banda, driver GeoTIFF, CRS horizontal definido, cuadrícula sin rotación.
- DTM para suelo desnudo; DSM para superficie con objetos. Declare correctamente el tipo.
- Datum vertical obligatorio y unidades `m` o `ft` (pie internacional, factor 0,3048).
- Valores de elevación sin escala/offset; reproyecte/convierta primero en QGIS cuando corresponda.
- Hasta 64 MB por archivo y 512 MB totales de importaciones por defecto. Máximo 100 millones de píxeles de origen, lectura recortada limitada a 4 millones.
- El archivo debe cubrir completamente la región. Si es demasiado detallado para el radio, reduzca el radio.

Seleccione el archivo de relieve en el panel; la fuente cambiará a **GeoTIFF local**. Para trabajar sin red puede desmarcar Overture y OSM y usar edificios más DEM locales. Las vías siguen requiriendo OSM.

### Ortofoto GeoTIFF

- Tres bandas RGB o cuatro RGBA, `uint8`, driver GeoTIFF y CRS definido.
- Debe ser una ortofoto ya corregida y lista para visualizar; City3D no realiza corrección radiométrica ni fotogrametría.
- Debe cubrir completamente el área solicitada y contar con una de las licencias admitidas.
- Se reproyecta a WGS84, se recorta a la región, se convierte a PNG y se incrusta en el GLB con fecha, atribución, licencia y SHA-256.
- La imagen se aplica solamente al relieve. Desde arriba produce una apariencia satelital; no añade fotografías laterales a las fachadas ni cambia las alturas.

Importe el archivo como **Ortofoto real** y selecciónelo en **Vista satelital / ortofoto**. Al terminar, el visor activa el estilo **Satelital · ortofoto**. No se descargan ni copian teselas de Google Maps: use una fuente cuya licencia permita la exportación y redistribución.

## Seguridad y despliegue

La importación está disponible por defecto solo para conexiones de desarrollo desde loopback y nombre de host local. En un servidor compartido permanece desactivada; `CITY3D_LOCAL_IMPORTS_ENABLED=true` requiere proteger el servicio con autenticación, cuotas y control de acceso externo. No habilitarlo en un Render público sin esa protección. No se implementó autenticación multiusuario en esta entrega.

Se comprueba `Origin` cuando está presente; no sustituye autenticación. Las rutas se generan en el servidor con IDs aleatorios, no con nombres ni rutas del cliente. No se admiten VRT/XML, URLs de archivos suministradas por el usuario ni referencias raster externas. La carga se limita durante el streaming, solo se publica tras validar y se limpia si falla. El bloqueo y la cuota son para un proceso local; no constituyen una cuota distribuida.

Los datasets se guardan bajo `data/imports`, excluidos de Git. En hosting efímero se pierden al reiniciar/desplegar sin almacenamiento persistente. Los trabajos que los referencien requerirán reimportación. No se subieron datos ni se desplegó este cambio.

## Arquitectura y decisiones

- `datasets/store.py`: contrato y validación de importaciones; archivos inmutables y manifiestos con hash.
- `api/datasets.py`: streaming acotado y publicación del archivo validado.
- `providers/local.py`: normalización de edificios locales.
- `providers/raster_dem.py`: lectura por ventanas, reproyección, Copernicus y GeoTIFF local.
- `providers/imagery.py`: validación de cobertura, recorte y reproyección de ortofoto local.
- `providers/worldcover.py`: clasificación categórica y caché.
- `conflation/service.py`: índice STRtree de candidatos, decisiones y prioridades por atributo. No modifica los objetos originales de los proveedores.
- `jobs/service.py`: orquestación y fallbacks explícitos, sin mezclar CRS/datums verticales.
- `generation/glb.py`: apoyo DTM/DSM, UV, textura embebida, clases WorldCover y metadatos inspeccionables.
- `features/data-sources/LocalDatasets.tsx`: formulario y selección independientes de la pantalla principal; envío en evento, no efecto React.

**Errores aprendidos:** no comparar una unión de referencias OSM contra sí misma al fusionar (podía absorber vecinos); no cambiar altura sin cambiar su categoría; no interpretar pies como metros; no asignar confianza numérica arbitraria; heredar metadatos de grupos GLB cuando el terreno tiene varios materiales; no compartir nombres de temporales entre escritores de caché.

## Límites pendientes (no implementados)

- Descarga directa selectiva de Microsoft Global Footprints y Google Open Buildings para complementar huecos realmente demostrados. Overture ya integra parte de estas fuentes.
- Estimaciones automáticas TEMPO / Google 2.5D: no se activaron. TEMPO global público tiene celdas de aproximadamente 100 m y no aporta alturas individuales medidas.
- Importación directa LAS/LAZ, GeoPackage, Shapefile, PBF y GeoParquet. Para esta versión, convierta huellas a GeoJSON o terreno a GeoTIFF en una herramienta GIS autorizada.
- Diferencias DSM−DTM: requieren compatibilidad vertical, temporal y resolución; no se calculan automáticamente.
- Tejados y partes de edificios, puentes/túneles con cotas propias, texturas de fachada, fotogrametría e incertidumbre métrica calibrada.
- Sectores grandes, workers distribuidos, cuotas multiusuario, limpieza gráfica de datasets y autenticación.
- Verificación visual del navegador y apertura final en Blender/Godot.

No se declara exactitud catastral ni reconstrucción fotorealista o completa de todo el mundo.

## Referencias verificadas

- [Copernicus COG y resolución](https://copernicus-dem-30m.s3.amazonaws.com/readme.html)
- [Copernicus: cobertura pública, DSM y licencia](https://registry.opendata.aws/copernicus-dem/)
- [ESA WorldCover: acceso, versiones y atribución](https://esa-worldcover.org/en/data-access)
- [TEMPO: resolución, bandas y condiciones](https://github.com/microsoft/buildings)
- [Overture: esquema y procedencia](https://docs.overturemaps.org/schema/reference/buildings/building/)
- [OSM: altura y unidades](https://wiki.openstreetmap.org/wiki/Key:height)
