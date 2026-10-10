# PROMPT MAESTRO DEFINITIVO — CITY3D ENGINE
## Plataforma geoespacial multifuente para generar, visualizar y exportar ciudades 3D reales

**Versión:** 2.0 — Arquitectura multifuente  
**Tipo de proyecto:** Aplicación web full-stack, GIS, generación procedural 3D y procesamiento geoespacial  
**Licenciamiento objetivo:** Software open source, herramientas gratuitas y fuentes de datos compatibles con uso comercial  
**Entorno principal:** Windows 10/11  
**Resultado esperado:** Aplicación funcional, código fuente completo, modelos 3D reales y pruebas verificables.

---

# 1. ROL DEL AGENTE

Actúa como un equipo de ingeniería senior compuesto por los siguientes especialistas:

- Arquitecto de software full-stack.
- Ingeniero GIS y especialista en sistemas de información geográfica.
- Ingeniero de procesamiento geoespacial y teledetección.
- Especialista en OpenStreetMap, Overture Maps y datos geográficos abiertos.
- Ingeniero de gráficos 3D especializado en Three.js, WebGL, WebGPU y geometría computacional.
- Ingeniero de generación procedural de escenarios.
- Especialista en modelos digitales de elevación (DEM).
- Ingeniero backend experto en Python y FastAPI.
- Desarrollador frontend experto en React y TypeScript.
- Ingeniero DevOps, automatización y pruebas.
- Especialista en optimización de modelos 3D y formatos glTF/GLB.

Tu misión es **diseñar, desarrollar, ejecutar, verificar y documentar una plataforma llamada City3D Engine**.

No debes limitarte a crear una maqueta, demostración visual o propuesta arquitectónica.

Debes construir una aplicación real que permita obtener información geográfica desde diferentes fuentes gratuitas, convertirla en escenarios tridimensionales, visualizarlos y exportarlos.

Trabaja con autonomía, utilizando las herramientas de desarrollo, búsqueda, terminal, repositorios y documentación que tengas disponibles.

# 2. OBJETIVO GENERAL

Desarrollar una plataforma web que permita generar automáticamente escenarios tridimensionales de ubicaciones reales de cualquier parte del mundo donde existan datos geográficos suficientes.

El usuario debe poder:

1. Introducir coordenadas de latitud y longitud.
2. Buscar una ciudad o ubicación.
3. Seleccionar una región geográfica.
4. Elegir qué información quiere representar.
5. Obtener datos desde varias bases geográficas gratuitas.
6. Comparar, complementar y unificar esos datos.
7. Generar edificios y estructuras 3D.
8. Incorporar elevaciones, montañas y pendientes reales.
9. Incorporar carreteras, caminos, áreas verdes y cuerpos de agua.
10. Explorar el escenario en tiempo real.
11. Inspeccionar los edificios y sus propiedades.
12. Cambiar estilos visuales y niveles de detalle.
13. Descargar el escenario en formato GLB.
14. Utilizar el modelo en Blender, Godot 4 y otros motores compatibles.
15. Conservar las referencias geográficas originales y conocer la procedencia de los datos.

La aplicación debe permitir trabajar inicialmente con zonas pequeñas, pero su arquitectura debe admitir una expansión posterior hacia barrios, ciudades y territorios más extensos.

**Principio fundamental:** no asumir que OpenStreetMap contiene toda la información necesaria para reconstruir una región.

El sistema debe utilizar una arquitectura geoespacial multifuente capaz de detectar información faltante e incorporar fuentes complementarias.

# 3. RESTRICCIONES FUNDAMENTALES

Cumple obligatoriamente estas condiciones:

- No utilizar APIs comerciales de pago como requisito obligatorio.
- No depender de suscripciones.
- No exigir tarjetas bancarias para utilizar el sistema localmente.
- Priorizar herramientas gratuitas y open source.
- Permitir ejecución en Windows 10/11 sin Docker ni WSL obligatorios.
- Permitir descargar y procesar datos geográficos locales.
- Evitar depender exclusivamente de un proveedor externo.
- Respetar límites y políticas de los servicios públicos.
- Mantener funcional el sistema cuando una fuente secundaria no esté disponible.
- No utilizar datos con restricciones comerciales incompatibles en el flujo predeterminado.
- Registrar las licencias de los conjuntos de datos utilizados.
- No utilizar imágenes o mapas comerciales de Google Earth, Google Maps u otros servicios como fuente no autorizada de geometrías o texturas.
- No presentar geometrías estimadas como mediciones exactas.
- No generar edificios inexistentes para ocultar la falta de datos.
- No afirmar que un modelo es fotorealista cuando únicamente se construyó mediante extrusión de polígonos.
- No afirmar que una función está implementada sin haberla probado.
- No integrar datos de licencias incompatibles sin resolver sus obligaciones.

El objetivo es que el desarrollo y el funcionamiento local puedan realizarse sin gastos obligatorios de licencias, infraestructura o API.

El sistema debe informar cuando un proveedor gratuito tenga límites de solicitudes, descargas, acceso o condiciones adicionales.

# 4. INVESTIGACIÓN INICIAL OBLIGATORIA

Antes de programar, investiga estas referencias.

## 4.1. Repositorio map3d

https://github.com/cartesiancs/map3d

Inspecciona:

- Arquitectura React.
- Uso de React Three Fiber.
- Selección de áreas mediante Leaflet.
- Integración con Overpass.
- Generación de geometrías mediante Three.js.
- Extrusión de edificios.
- Generación de carreteras.
- Navegación tridimensional.
- Exportación mediante GLTFExporter.
- Manejo de estados.

Archivos importantes:

- `src/three/Space.tsx`
- `src/three/Car.tsx`
- `src/components/map/SelectMap.tsx`
- `src/ui/App.tsx`

Identifica componentes reutilizables.

Corrige sus limitaciones, especialmente:

- Factores arbitrarios de escala geográfica.
- Posibles distorsiones horizontales y verticales.
- Tratamiento incorrecto de alturas.
- Ausencia de relieve.
- Manejo limitado de geometrías complejas.
- Carreteras representadas únicamente mediante líneas.
- Materiales uniformes.
- Falta de optimización para grandes regiones.

No copies problemas arquitectónicos simplemente por reutilizar el repositorio.

## 4.2. OSM2World

https://github.com/tordanik/OSM2World

https://osm2world.org/

Investiga:

- Conversión de datos OSM a modelos 3D.
- Formatos admitidos.
- Exportación GLB/glTF.
- Materiales.
- Edificios con tejados.
- Carreteras.
- Terreno.
- Soporte de elevación.
- Configuración de su CLI.
- Compatibilidad con Windows.
- Posibilidades de integración mediante procesos externos.

Verifica los comandos correspondientes a la versión realmente instalada.

No presupongas que una misma interfaz CLI funciona en todas las versiones.

## 4.3. Overture Maps

https://overturemaps.org/

https://docs.overturemaps.org/

https://explore.overturemaps.org/

Investiga:

- Esquema de edificios.
- Edificios parciales.
- Atributos de altura.
- Identificadores GERS.
- Sistema de procedencia.
- GeoParquet.
- Descargas geográficas.
- Versionado y publicaciones.
- Licencias.
- Conflación de datos provenientes de varias fuentes.

Presta especial atención al hecho de que Overture ya integra información procedente de OpenStreetMap y proveedores como Microsoft y Google.

**No descargues nuevamente esas fuentes para incorporarlas indiscriminadamente sobre Overture.**

## 4.4. Otras referencias

- https://www.openstreetmap.org/
- https://overpass-turbo.eu/
- https://download.geofabrik.de/
- https://github.com/microsoft/GlobalMLBuildingFootprints
- https://sites.research.google/gr/open-buildings/
- https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1
- https://www.esa-worldcover.org/
- https://www.usgs.gov/
- https://registry.opendata.aws/
- https://threejs.org/
- https://github.com/pmndrs/react-three-fiber
- https://docs.godotengine.org/
- https://www.blender.org/

Consulta la documentación oficial vigente y contrasta las capacidades reales de cada proyecto.

# 5. ARQUITECTURA GEOESPACIAL MULTIFUENTE

Esta es una de las características más importantes del sistema.

City3D Engine debe incorporar una arquitectura modular que permita utilizar varias bases de datos geográficas.

No quiero una aplicación limitada exclusivamente a OpenStreetMap.

Diseña un **Geospatial Multi-Source Engine**.

Este motor debe:

- Seleccionar proveedores.
- Consultar información disponible.
- Determinar cobertura.
- Descargar datos.
- Normalizar geometrías.
- Detectar elementos duplicados.
- Resolver conflictos.
- Completar atributos.
- Registrar procedencia.
- Calcular indicadores de calidad.
- Entregar un modelo geográfico unificado al generador 3D.

Cada proveedor debe implementarse como un adaptador independiente.

Un fallo de un proveedor no debe bloquear toda la generación cuando existan fuentes alternativas válidas.

# 6. PROVEEDORES DE DATOS GEOGRÁFICOS

## 6.1. Overture Maps — proveedor principal de edificios

Utiliza Overture Maps como fuente consolidada prioritaria de edificios cuando esté disponible.

Debe servir para obtener:

- Contornos de edificios.
- Edificios parciales.
- Identificadores.
- Alturas disponibles.
- Número de pisos cuando exista.
- Nombres.
- Atributos de construcción.
- Referencias a fuentes originales.

Utiliza su cliente oficial o consultas GeoParquet mediante DuckDB.

Prioriza descargas por bounding box y transferencia selectiva.

Registra:

- Versión o release de Overture.
- Identificador de edificio.
- Identificador GERS cuando exista.
- Procedencia reportada.
- Fecha del conjunto de datos.
- Licencia aplicable.

No asumas que todos los edificios tienen altura.

No asumas que un polígono detectado por satélite corresponde exactamente a las paredes de la construcción; algunos pueden representar contornos de tejados.

## 6.2. OpenStreetMap — cartografía y enriquecimiento

Utiliza OSM para:

- Carreteras.
- Calles.
- Senderos.
- Edificios.
- Edificios parciales.
- Puentes.
- Túneles.
- Ferrocarriles.
- Ríos.
- Parques.
- Zonas residenciales.
- Usos de suelo.
- Atributos arquitectónicos.
- Nombres y propiedades relevantes.

Emplea Overpass para áreas pequeñas y archivos OSM/PBF para procesamiento regional.

Cuando Overture ya contenga un edificio procedente de OSM, detecta esa equivalencia.

No representes dos edificios superpuestos.

Los datos de OSM pueden utilizarse para enriquecer la geometría de Overture, o sustituirla cuando existan razones documentadas.

Conserva siempre la procedencia original.

## 6.3. Microsoft Global Building Footprints — proveedor complementario

Referencia:

https://github.com/microsoft/GlobalMLBuildingFootprints

Utiliza este conjunto de datos para completar edificios faltantes cuando corresponda.

Admite:

- Polígonos disponibles.
- Descargas por regiones y particiones.
- Filtrado espacial.
- Validación geométrica.
- Comparación con edificios existentes.

Comprueba si los edificios ya están incorporados en la versión de Overture utilizada.

Utiliza Microsoft directamente solo cuando aporte información adicional verificable.

Registra su licencia CDLA Permissive 2.0 y la procedencia correspondiente.

No asumas que todos los registros incluyen alturas.

## 6.4. Google Open Buildings — polígonos

Referencia:

https://sites.research.google/gr/open-buildings/

Permite utilizar los datos de polígonos cuando exista cobertura relevante y la licencia lo permita.

Debes:

- Consultar la disponibilidad geográfica.
- Comprobar si Overture ya incorporó esos edificios.
- Filtrar detecciones de baja confianza.
- Evitar duplicados.
- Registrar puntuaciones de confianza cuando existan.
- Identificar posibles falsos positivos.
- Respetar las condiciones y atribuciones.

No confundas los polígonos de Google Open Buildings con su conjunto de datos temporal 2.5D.

Son productos distintos y requieren adaptadores distintos.

## 6.5. Google Open Buildings 2.5D Temporal — estimación de alturas

Referencia:

https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1

Utiliza este conjunto como fuente complementaria de estimaciones.

Incluye información raster de:

- Presencia de construcciones.
- Conteos fraccionarios.
- Alturas estimadas.
- Variación temporal.

No lo interpretes como una base de polígonos exactos ni como alturas medidas individualmente por edificio.

Debes implementar un proceso geoespacial que permita:

1. Identificar las celdas que intersectan un edificio.
2. Extraer valores válidos.
3. Evaluar la confianza y la cobertura de la observación.
4. Aplicar una agregación espacial razonable.
5. Obtener una estimación cuando técnicamente esté justificado.
6. Identificar el resultado como estimado.
7. Registrar año, resolución, incertidumbre y procedencia.

No utilices este proveedor si su acceso, licencia o condiciones actuales resultan incompatibles con el proyecto.

Debe ser opcional y estar desacoplado.

## 6.6. GlobalBuildingAtlas — proveedor experimental

Referencia:

https://github.com/zhu-xlab/GlobalBuildingAtlas

Investiga su información de:

- Polígonos.
- Alturas.
- Modelos LoD1.

Este proveedor requiere especial atención a las licencias.

Algunos subconjuntos están bajo ODbL y otros bajo CC BY-NC 4.0.

**No actives por defecto los subconjuntos no comerciales.**

Si implementas compatibilidad, incorpórala como módulo experimental que:

- Identifique la licencia de cada subconjunto.
- Impida su uso en perfiles incompatibles.
- Solicite configuración explícita.
- Preserve la procedencia.
- No combine silenciosamente información con restricciones incompatibles.

## 6.7. Fuentes oficiales y regionales

Desarrolla una interfaz para incorporar datos geográficos oficiales de países, gobiernos y municipios.

Para Ecuador, investiga inicialmente:

- Instituto Geográfico Militar del Ecuador.
- Geoportales gubernamentales.
- Geoportal Metropolitano de Quito.
- Instituciones públicas que publiquen cartografía abierta.
- Catastros municipales disponibles legalmente.
- Infraestructura de Datos Espaciales del Ecuador.

No asumas que una capa publicada en un geoportal puede descargarse, reutilizarse o redistribuirse libremente.

Verifica caso por caso.

Permite importar:

- GeoJSON.
- GeoPackage.
- Shapefile.
- GeoTIFF.
- OSM.
- PBF.
- GeoParquet.

Cuando corresponda, admite servicios WFS u OGC API Features.

No confundas un servicio WMS de visualización con una fuente de geometrías vectoriales descargables.

Estas fuentes deberán funcionar como adaptadores configurables.

# 7. ESTRATEGIA INTELIGENTE DE SELECCIÓN DE FUENTES

No consultes todas las bases indiscriminadamente.

Implementa una estrategia inteligente para reducir descargas, procesamiento y duplicación.

Flujo propuesto:

**Paso 1:** Identificar país, coordenadas, extensión y características de la región.

**Paso 2:** Consultar Overture Maps para obtener edificios consolidados.

**Paso 3:** Consultar OSM para vías, características del suelo y atributos complementarios.

**Paso 4:** Analizar cobertura y calidad de los elementos encontrados.

**Paso 5:** Detectar qué información falta realmente.

**Paso 6:** Seleccionar fuentes adicionales que puedan cubrir esas carencias.

**Paso 7:** Descargar únicamente los datos necesarios.

**Paso 8:** Unificar geometrías y atributos.

**Paso 9:** Registrar niveles de confianza y procedencia.

**Paso 10:** Enviar el resultado al generador 3D.

Ejemplo:

Si Overture ya proporciona el contorno de un edificio y OSM aporta su nombre y número de pisos, debemos generar un solo edificio enriquecido.

Si una fuente contiene un edificio que no aparece en la base consolidada, podemos añadirlo después de verificar que no sea un duplicado.

Si ninguna fuente conoce su altura, se podrá estimar, pero debe identificarse claramente.

El sistema debe seguir siendo funcional si solo existe una fuente utilizable.

# 8. MOTOR DE FUSIÓN Y NORMALIZACIÓN GEOESPACIAL

Implementa un módulo central denominado:

**Geospatial Fusion Engine**

Responsabilidades:

- Transformar geometrías al sistema de referencia común.
- Validar polígonos.
- Reparar geometrías cuando sea seguro.
- Identificar geometrías inválidas no reparables.
- Detectar duplicados.
- Resolver superposiciones.
- Asociar edificios entre proveedores.
- Fusionar atributos.
- Determinar qué geometría utilizar.
- Registrar decisiones de fusión.
- Conservar las fuentes originales.
- Generar objetos geoespaciales normalizados.

Utiliza herramientas como:

- Shapely.
- GeoPandas, cuando sea apropiado.
- PyProj.
- DuckDB Spatial.
- PyArrow.
- Rasterio.
- PyOsmium.

## 8.1. Modelo unificado de edificios

Cada edificio normalizado debe disponer, cuando corresponda, de:

- Identificador interno.
- Identificadores originales.
- Geometría.
- Coordenadas geográficas.
- CRS de origen.
- Altura.
- Tipo de altura.
- Número de pisos.
- Forma del techo.
- Altura del techo.
- Material.
- Color.
- Fecha o versión de datos.
- Fuente de la geometría.
- Fuente de cada atributo.
- Indicador de confianza.
- Estado de validación.
- Licencia de origen.
- Relaciones con edificios parciales.
- Historial de conflictos y decisiones.

La procedencia debe almacenarse **por atributo**, no únicamente por edificio.

Por ejemplo, la geometría puede proceder de Overture y la altura de OSM.

## 8.2. Detección de duplicados

Implementa detección espacial mediante técnicas como:

- Intersección de polígonos.
- Intersection over Union (IoU).
- Distancia entre centroides.
- Comparación de áreas.
- Identificadores originales.
- Identificadores GERS.
- Correspondencia con referencias OSM.
- Relaciones de edificio y sus partes.

No utilices exclusivamente igualdad de coordenadas.

No establezcas un único umbral fijo sin analizar su efecto.

Un edificio grande puede tener varias secciones; dos construcciones distintas pueden compartir paredes.

Evita eliminar incorrectamente edificios adyacentes.

Distingue:

- Duplicados reales.
- Edificios contiguos.
- Edificios anidados.
- Partes de edificios.
- Polígonos de tejados.
- Geometrías antiguas.
- Conflictos no resueltos.

Registra las decisiones de fusión y permite inspeccionarlas.

## 8.3. Prioridad de fuentes

No utilices una prioridad rígida universal sin considerar la calidad.

Implementa una política configurable que evalúe:

- Calidad geométrica.
- Origen del dato.
- Actualidad.
- Precisión declarada.
- Información disponible.
- Confiabilidad.
- Compatibilidad legal.
- Consistencia con fuentes complementarias.

Da preferencia razonable a geometrías oficiales verificadas o cartografía manual de calidad frente a predicciones automáticas, pero permite resolver conflictos según evidencia.

Nunca sustituyas silenciosamente una altura explícita de una fuente fiable por otra estimada.

# 9. EVALUACIÓN DE COBERTURA Y CALIDAD

Crea un módulo denominado:

**Geospatial Data Quality Analyzer**

Debe evaluar:

- Número de edificios encontrados.
- Número de edificios únicos después de la fusión.
- Número de edificios incorporados por fuente.
- Porcentaje de edificios con altura explícita.
- Porcentaje de edificios con alturas estimadas.
- Cantidad de conflictos.
- Cantidad de geometrías inválidas.
- Cobertura del terreno.
- Disponibilidad del DEM.
- Cobertura de vías.
- Existencia de información de vegetación.
- Antigüedad de los conjuntos de datos.
- Advertencias de licencia.

No presentes un porcentaje de cobertura real si desconoces el número verdadero de edificios existentes.

Diferencia entre:

- Cobertura observada en las fuentes.
- Completitud de atributos.
- Calidad geométrica estimada.
- Cobertura respecto a una referencia independiente, cuando exista.

La interfaz debe mostrar un resumen de calidad antes y después de generar el escenario.

Los indicadores deben ser reproducibles y no inventados.

# 10. GENERACIÓN AUTOMÁTICA DE EDIFICIOS 3D

El motor 3D debe procesar los datos normalizados y construir geometrías tridimensionales reales.

Soporta:

- Edificios rectangulares.
- Edificios irregulares.
- Edificios con patios internos.
- Multipolígonos.
- Edificios con partes.
- Construcciones de diferentes alturas.
- Tejados simples.
- Tejados inclinados cuando haya información.
- Construcciones sobre terrenos inclinados.

La geometría debe ser cerrada y tener normales correctas cuando el uso previsto lo requiera.

Evita:

- Duplicaciones.
- Extrusiones invertidas.
- Huecos no deseados.
- Intersecciones incorrectas.
- Objetos colocados bajo el terreno.
- Distorsiones de escala.
- Pisos con alturas arbitrarias no documentadas.

## 10.1. Estrategia de alturas

Implementa un sistema de prioridades y confianza.

Categorías:

**A. Altura explícita fiable**

Utilizar cuando se dispone de una altura válida y consistente.

**B. Altura derivada de atributos**

Calcular mediante número de pisos y una altura por piso configurable, si no existe una altura explícita fiable.

**C. Altura estimada por datos espaciales**

Utilizar datos raster o estimaciones de otras fuentes cuando el método sea técnicamente válido.

**D. Altura desconocida**

Utilizar un valor visual configurable cuando sea indispensable para representar el edificio.

Este valor nunca debe etiquetarse como altura real.

Cada edificio debe registrar su categoría.

Incluye una opción para visualizar los edificios con colores según la fiabilidad de sus alturas.

## 10.2. Nivel de detalle

Implementa tres niveles:

**LOD0 — Volúmenes básicos**

Extrusión sencilla, pocos polígonos y materiales simples.

**LOD1 — Arquitectura básica**

Formas generales de edificios y tejados cuando existan suficientes atributos.

**LOD procedural — Representación estilizada**

Fachadas, ventanas y materiales generados proceduralmente.

La representación procedural no debe interpretarse como reconstrucción exacta.

No inventes detalles arquitectónicos como si procedieran de observaciones reales.

# 11. TERRENO, RELIEVE Y ELEVACIÓN

Desarrolla un sistema de generación de terrenos a partir de DEM.

Fuentes recomendadas:

- NASA/USGS SRTM.
- Copernicus DEM cuando su acceso y condiciones sean adecuados.
- Modelos digitales de elevación oficiales.
- Archivos GeoTIFF/HGT proporcionados por el usuario.

Funcionalidades:

- Localizar los archivos necesarios.
- Descargar datos dentro de las condiciones permitidas.
- Permitir archivos DEM locales.
- Leer metadatos geográficos.
- Recortar el área seleccionada.
- Reproyectar.
- Interpretar correctamente unidades y datum vertical.
- Gestionar valores NoData.
- Generar una malla triangular.
- Ajustar resolución.
- Construir pendientes.
- Ubicar elementos sobre la superficie.

El sistema no debe asignar alturas incompatibles si los datos geográficos utilizan distintos datums verticales.

## 11.1. Integración de edificios con terreno

Los edificios deben posicionarse correctamente respecto a la elevación.

Debes investigar y gestionar situaciones como:

- Edificios sobre terrenos inclinados.
- Bases que requieren nivelación local.
- Entradas a distinta altura.
- Edificios sobre plataformas.
- Carreteras elevadas.
- Puentes.
- Túneles.
- Terrenos con elevaciones faltantes.

Evita que los edificios aparezcan flotando o enterrados.

Cuando la resolución del DEM no permita representar un detalle de forma fiable, documenta esa limitación.

## 11.2. Respaldo sin DEM

Si no se encuentra información de elevación válida:

- Ofrece generar una escena plana.
- Indica que el relieve real no está disponible.
- No inventes montañas ni pendientes.
- Conserva las coordenadas originales.

# 12. VEGETACIÓN, AGUA Y COBERTURA DEL SUELO

Integra ESA WorldCover como proveedor complementario de clasificación de superficie.

Referencia:

https://esa-worldcover.org/

Utiliza sus categorías para identificar aproximadamente:

- Bosques.
- Árboles.
- Praderas.
- Cultivos.
- Áreas urbanizadas.
- Suelo desnudo.
- Agua.
- Humedales.
- Otras coberturas disponibles.

Implementa un generador procedural de ambientación.

Debe permitir:

- Distribuir vegetación en zonas apropiadas.
- Evitar colocar árboles dentro de edificios.
- Evitar árboles en carreteras.
- Generar superficies diferenciadas.
- Representar cuerpos de agua.
- Aplicar materiales al suelo.
- Desactivar elementos decorativos.

No interpretes ESA WorldCover como un inventario de árboles individuales.

La vegetación generada será aproximada y debe distinguirse de objetos cartografiados individualmente en OSM.

Utiliza técnicas de instancing para evitar miles de objetos independientes.

Permite elegir entre:

- Sin vegetación.
- Vegetación simplificada.
- Vegetación procedural optimizada.

# 13. SISTEMA DE COORDENADAS Y PRECISIÓN GEOGRÁFICA

Implementa un sistema de coordenadas geográficas riguroso.

Requisitos:

- Utilizar WGS84 para intercambio de coordenadas geográficas.
- Aplicar proyecciones métricas adecuadas.
- Seleccionar un origen local.
- Mantener precisión relativa.
- Evitar factores arbitrarios.
- Definir el eje vertical.
- Evitar invertir direcciones.
- Gestionar zonas UTM correctamente.
- Soportar regiones próximas a límites entre zonas.
- Conservar metadatos de georreferenciación.

Para Sangolquí se puede utilizar EPSG:32717 cuando resulte adecuado.

No utilices automáticamente esa proyección para cualquier ciudad del mundo.

Evalúa la proyección apropiada para cada caso o emplea un sistema local ENU bien definido.

En Three.js, utiliza una convención coherente de ejes y documenta la transformación hacia los sistemas de Blender y Godot.

Crea pruebas para verificar distancias conocidas y alturas.

Ejemplo de requisito:

Un edificio cuyo contorno mida 20 metros por 10 metros debe conservar aproximadamente esas dimensiones al exportarse.

Incluye tolerancias de prueba justificadas.

# 14. MOTOR DE GENERACIÓN 3D

Desarrolla un componente desacoplado denominado:

**3D Scene Generation Engine**

Este motor debe recibir los datos geográficos normalizados y generar los modelos correspondientes.

Prioriza OSM2World cuando sea apropiado.

Sin embargo, no supongas que puede procesar directamente datos GeoParquet, Shapefile o geometrías fusionadas arbitrarias.

Implementa adaptadores de conversión.

Arquitectura posible:

Datos multifuente → Geometrías normalizadas → Adaptador de generación → Mallas 3D → Modelo GLB.

Evalúa dos estrategias:

**Estrategia A: OSM2World**

Convertir los datos compatibles a representaciones que pueda procesar OSM2World.

**Estrategia B: Generador geométrico propio**

Construir las mallas mediante bibliotecas geoespaciales y Three.js u otras herramientas adecuadas.

Elige una estrategia principal después de una prueba técnica.

La segunda podrá servir para elementos que el motor principal no soporte.

No intentes crear archivos OSM sintéticos inválidos para introducir datos de otras fuentes.

Si conviertes datos fusionados a una representación OSM intermedia, utiliza identificadores internos controlados, geometrías válidas y pruebas de importación.

Diseña una interfaz común para ambos generadores.

La meta es producir modelos GLB correctos y reutilizables, no depender obligatoriamente de una única biblioteca.

# 15. VISOR 3D INTERACTIVO

Desarrolla un visor mediante Three.js y React Three Fiber.

Debe permitir:

- Vista orbital.
- Vista superior.
- Vista isométrica.
- Cámara libre.
- Zoom.
- Paneo.
- Rotación.
- Navegación en primera persona.
- Movimiento WASD.
- Control de velocidad.
- Restablecimiento de cámara.
- Selección de objetos.
- Inspector de edificios.
- Activación y desactivación de capas.
- Visualización de alturas.
- Visualización de procedencia.
- Visualización de datos estimados.

Implementa iluminación y sombras configurables.

Incorpora estilos:

**Cartográfico:** edificios simples y colores funcionales.

**Arquitectónico:** materiales y detalles mejorados.

**Nocturno:** iluminación ambiental oscura y elementos resaltados.

**Análisis GIS:** colores según altura, calidad, fuente o clasificación.

Los estilos deben compartir la misma información geográfica.

No vuelvas a consultar o generar todos los datos únicamente para cambiar un material visual.

# 16. INTERFAZ DE USUARIO

Diseña una herramienta profesional.

Nombre:

**City3D Engine**

Identidad visual:

- Tema oscuro.
- Colores grafito, azul y blanco.
- Interfaz limpia.
- Paneles técnicos.
- Botones identificables.
- Animaciones discretas.
- Visor tridimensional como protagonista.
- Indicadores de procesamiento.
- Diseño adaptable.

## Panel izquierdo

- Buscar ubicación.
- Coordenadas.
- Selección de región.
- Radio.
- Fuentes de información.
- Configuración del terreno.
- Configuración de generación.

## Panel central

- Vista 2D.
- Vista 3D.
- Herramientas de cámara.
- Controles de navegación.
- Selección de edificios.
- Vista de progreso.

## Panel derecho

- Detalles de la región.
- Número de edificios.
- Fuentes consultadas.
- Cobertura disponible.
- Datos faltantes.
- Alturas estimadas.
- Calidad geográfica.
- Propiedades del objeto seleccionado.
- Opciones de exportación.

## Panel inferior

- Estado de trabajos.
- Errores.
- Advertencias.
- Progreso.
- Cancelación.
- Descargas.

Incorpora una vista de **comparación de fuentes**, donde el usuario pueda identificar:

- Edificios encontrados en Overture.
- Edificios aportados por OSM.
- Edificios adicionales provenientes de fuentes complementarias.
- Edificios descartados como duplicados.
- Edificios con conflictos.
- Edificios con alturas estimadas.

# 17. SELECTOR GEOGRÁFICO

Implementa una herramienta que permita:

- Introducir latitud y longitud.
- Seleccionar una ubicación en un mapa.
- Seleccionar un rectángulo.
- Definir un radio.
- Buscar un lugar por nombre mediante un proveedor compatible.
- Mostrar área seleccionada.
- Ver coordenadas de los límites.
- Estimar complejidad.

Radios iniciales:

- 100 metros.
- 250 metros.
- 500 metros.
- 1.000 metros.

Permite personalización dentro de límites seguros.

Para el MVP, utiliza una extensión reducida.

No habilites procesamiento ilimitado de grandes ciudades sin mecanismos de partición y control de recursos.

# 18. EXPORTACIÓN DE ESCENARIOS

Implementa exportación real de modelos tridimensionales.

Formatos:

**Obligatorios:**
- GLB.
- JSON de metadatos geográficos.

**Opcionales:**
- glTF.
- OBJ.
- ZIP con todos los archivos.
- Formatos adicionales mediante convertidores compatibles.

El usuario debe poder elegir:

- Edificios.
- Carreteras.
- Terreno.
- Vegetación.
- Agua.
- Materiales.
- Nivel de detalle.
- Región completa o parte del escenario.

Todos los archivos deben conservar dimensiones coherentes.

El JSON complementario debe incluir:

- Coordenadas de origen.
- CRS utilizado.
- Unidades.
- Convención de ejes.
- Bounding box.
- Fuentes utilizadas.
- Versiones de los datasets.
- Indicadores de calidad.
- Fecha de generación.
- Información de licencias.
- Relación entre identificadores de objetos 3D y entidades geográficas.
- Advertencias sobre alturas estimadas.

Exporta mallas reales y no imágenes del visor.

Valida que los modelos puedan abrirse e importarse.

El objetivo es poder cargar un escenario en Blender o Godot sin reconstruir manualmente sus edificios y carreteras.

# 19. SISTEMA DE CACHÉ Y FUNCIONAMIENTO LOCAL

Implementa almacenamiento local para evitar descargas repetidas.

Capas de caché:

1. Consultas geográficas.
2. Archivos de fuentes originales.
3. Geometrías normalizadas.
4. Modelos de elevación.
5. Resultados de fusión.
6. Geometrías generadas.
7. Modelos GLB.

La caché debe identificar:

- Región.
- Proveedores.
- Versión de datos.
- Parámetros de generación.
- Estilo geométrico.
- Versión del generador.

No reutilices incorrectamente datos de una región para otra.

Permite:

- Eliminar caché.
- Consultar su tamaño.
- Regenerar escenarios.
- Trabajar con datos locales.
- Inspeccionar versiones.

Un escenario previamente generado debe poder visualizarse sin conexión siempre que todos sus archivos necesarios estén disponibles.

# 20. RENDIMIENTO Y GRANDES REGIONES

Implementa progresivamente:

- Procesamiento por sectores.
- Carga bajo demanda.
- Niveles de detalle.
- Simplificación.
- Reutilización de geometrías.
- Instancing.
- Compresión compatible de modelos.
- Caché.
- Procesamiento paralelo controlado.
- Gestión de memoria.
- Eliminación de recursos no utilizados.
- Cancelación de tareas.

No construyas toda una ciudad como un único objeto monolítico si eso afecta rendimiento y reutilización.

El sistema debe estar preparado para generar paquetes por sectores y después visualizarlos como un escenario lógico único.

Evita que el frontend se bloquee durante una conversión.

Cuando una región sea demasiado extensa, informa al usuario y ofrece dividirla automáticamente.

# 21. BACKEND Y API

Utiliza preferentemente Python y FastAPI.

Implementa una API REST versionada.

Endpoints sugeridos:

- `GET /api/health`
- `GET /api/capabilities`
- `GET /api/providers`
- `POST /api/regions/preview`
- `POST /api/datasets/inspect`
- `POST /api/generations`
- `GET /api/generations/{id}`
- `POST /api/generations/{id}/cancel`
- `GET /api/generations/{id}/model`
- `GET /api/generations/{id}/metadata`
- `GET /api/generations/{id}/quality`
- `GET /api/generations/{id}/sources`

El sistema debe incluir:

- Validación de entradas.
- Gestión de trabajos.
- Estados de procesamiento.
- Timeouts.
- Reintentos limitados.
- Manejo de excepciones.
- Logs.
- Almacenamiento temporal.
- Limpieza de trabajos.
- Caché.
- Control de concurrencia.

Los estados pueden ser:

- pending
- downloading
- normalizing
- merging
- processing_terrain
- generating
- validating
- completed
- failed
- cancelled

Implementa persistencia de trabajos y control de procesos externos.

No dependas de una única petición HTTP de larga duración.

Cuando ejecutes OSM2World, utiliza procesos externos controlados mediante argumentos seguros.

Evita comandos shell construidos mediante concatenación de entradas del usuario.

# 22. LICENCIAS Y TRAZABILIDAD

Implementa un **Data Licensing and Provenance Manager**.

Este módulo debe registrar:

- Proveedor.
- Dataset.
- Versión.
- Licencia.
- URL de origen.
- Fecha de descarga.
- Condiciones de atribución.
- Restricciones.
- Identificadores originales.
- Transformaciones aplicadas.
- Información necesaria para cumplir obligaciones de redistribución.

Presta especial atención a:

**OpenStreetMap:** ODbL.

**Overture Buildings:** ODbL y sus requisitos aplicables.

**Microsoft Building Footprints:** CDLA Permissive 2.0.

**ESA WorldCover:** CC BY 4.0.

**Google Open Buildings:** verificar los términos específicos del producto y versión utilizados.

**GlobalBuildingAtlas:** distinguir sus subconjuntos ODbL y CC BY-NC 4.0.

**Datos oficiales:** verificar individualmente.

No asumas que todas las fuentes gratuitas pueden mezclarse y redistribuirse sin obligaciones adicionales.

Un GLB puede constituir una obra producida a partir de una base geográfica. Analiza las obligaciones de atribución y disponibilidad de bases derivadas correspondientes, en particular cuando se utilice OSM/ODbL.

Implementa perfiles:

**Perfil compatible con uso comercial**

Solo fuentes cuya licencia permita el uso previsto, cumpliendo sus condiciones.

**Perfil de investigación**

Permite activar explícitamente conjuntos adicionales cuando sus licencias y el uso concreto lo permitan.

El perfil de investigación no debe servir para eludir restricciones de licencia.

Ante incompatibilidades no resueltas, bloquea la combinación o exportación afectada e informa la causa.

Incluye un archivo de atribuciones descargable junto al modelo.

# 23. CALIDAD Y CONFIANZA VISUAL

La aplicación debe representar claramente la diferencia entre:

- Información observada.
- Información cartografiada manualmente.
- Información procedente de modelos de aprendizaje automático.
- Datos interpolados.
- Alturas estimadas.
- Geometría procedural decorativa.
- Información desconocida.

Implementa visualizaciones temáticas.

Ejemplo:

- Azul: geometría con atributos explícitos.
- Verde: datos complementados.
- Amarillo: altura estimada.
- Gris: información insuficiente.
- Rojo: conflicto no resuelto.

Estos colores pueden ajustarse en el diseño final.

Nunca presentes la calidad de un modelo únicamente a través de un porcentaje arbitrario.

Cada indicador debe tener una definición reproducible.

# 24. SEGURIDAD Y ROBUSTEZ

Valida:

- Coordenadas inválidas.
- Regiones excesivas.
- Geometrías corruptas.
- Archivos malformados.
- Datos demasiado grandes.
- Errores de red.
- Fallos de proveedores.
- Descargas interrumpidas.
- Dependencias faltantes.
- Conversión incompleta.
- DEM incompatibles.
- Problemas de licencia.
- Errores en exportación.
- Falta de espacio en disco.

Protege el backend contra:

- Path traversal.
- Ejecución arbitraria de comandos.
- Acceso a rutas no permitidas.
- Descargas desde destinos inseguros.
- Agotamiento accidental de memoria.
- Procesos que queden ejecutándose indefinidamente.

Limita tamaños de entrada y recursos.

Desarrolla mensajes comprensibles para el usuario, acompañados de diagnósticos técnicos en los logs.

# 25. STACK RECOMENDADO

## Frontend

- React.
- TypeScript.
- Vite.
- Tailwind CSS.
- Three.js.
- React Three Fiber.
- Drei.
- Zustand.
- Leaflet o MapLibre.
- TanStack Query cuando resulte apropiado.

## Backend

- Python 3.11 o superior.
- FastAPI.
- Pydantic.
- HTTPX.
- Shapely.
- PyProj.
- PyArrow.
- DuckDB Spatial.
- Rasterio.
- PyOsmium.
- GDAL cuando sea necesario.
- SQLite para persistencia local de trabajos y configuración, si resulta adecuado.

## Generación

- OSM2World.
- Herramientas de conversión geométrica.
- Three.js.
- Exportación glTF/GLB.
- Generación procedural para elementos complementarios.

## Infraestructura

- Windows.
- PowerShell.
- Node.js.
- Java compatible con OSM2World.
- Python.
- Git.

No agregues infraestructura compleja como Kubernetes, Redis o servicios en la nube si el MVP funciona correctamente sin ellos.

Las dependencias opcionales deben mantenerse opcionales.

# 26. ESTRUCTURA DEL PROYECTO

Organiza el repositorio como mínimo en módulos equivalentes a:

**city3d-engine/**

**frontend/**
- components/
- features/map/
- features/viewer/
- features/buildings/
- features/terrain/
- features/data-sources/
- features/quality/
- features/export/
- stores/
- hooks/
- services/
- types/

**backend/app/**
- api/
- core/
- providers/
- normalization/
- conflation/
- data_quality/
- projection/
- geometry/
- terrain/
- vegetation/
- generation/
- exporters/
- licensing/
- jobs/
- cache/
- models/

**backend/tests/**
- unit/
- integration/
- fixtures/
- e2e/

**data/**
- osm/
- overture/
- buildings/
- dem/
- landcover/
- cache/
- generated/

**scripts/**
- setup-windows.ps1
- start-dev.ps1
- check-dependencies.ps1
- run-tests.ps1

**docs/**
- architecture.md
- data-sources.md
- licensing.md
- georeferencing.md
- developer-guide.md
- user-guide.md
- validation-report.md

Además:

- README.md
- .env.example
- .gitignore
- LICENSE

Puedes mejorar la organización cuando exista una justificación técnica.

No subas al repositorio grandes conjuntos de datos descargados ni modelos generados por el usuario.

# 27. PLAN DE DESARROLLO OBLIGATORIO

Trabaja por fases, manteniendo una versión ejecutable.

## FASE 0 — Investigación y auditoría

- Inspeccionar el entorno.
- Revisar el código existente.
- Investigar OSM2World.
- Investigar Overture.
- Verificar acceso a fuentes.
- Revisar licencias.
- Validar herramientas disponibles.
- Seleccionar arquitectura.
- Documentar riesgos.

**Criterio de salida:** arquitectura justificada y prueba técnica de acceso a datos y generación de un archivo GLB mínimo.

## FASE 1 — Generador geográfico mínimo

- Interfaz React.
- Selector de coordenadas.
- Selección de área.
- API FastAPI.
- Descarga OSM.
- Generación de edificios.
- Generación de carreteras.
- Exportación GLB.
- Visor Three.js.

**Criterio de salida:** escenario generado a partir de coordenadas reales, visible y descargable.

## FASE 2 — Integración Overture

- Adaptador Overture.
- Descarga de edificios.
- Normalización.
- Integración OSM + Overture.
- Detección de duplicados.
- Registro de procedencia.
- Resolución inicial de conflictos.

**Criterio de salida:** una escena consolidada sin duplicación significativa de edificios.

## FASE 3 — Motor de datos complementarios

- Adaptador Microsoft.
- Adaptador Google Open Buildings.
- Detección de carencias.
- Consultas selectivas.
- Fusión avanzada.
- Análisis de calidad.
- Estimación de alturas opcional.

**Criterio de salida:** al menos una región donde se demuestre una mejora real de cobertura o atributos frente a utilizar solo OSM.

No declares mejora si las fuentes no aportaron elementos adicionales válidos.

## FASE 4 — Relieve real

- Datos SRTM.
- Importación GeoTIFF/HGT.
- Generación de malla.
- Integración de edificios y vías.
- Manejo de elevación.
- Exportación de terreno.

**Criterio de salida:** escena de una región con pendientes, georreferenciada y con elevaciones coherentes.

## FASE 5 — Ambientación

- ESA WorldCover.
- Clasificación de suelo.
- Vegetación procedural.
- Materiales.
- Agua.
- Estilos visuales.

**Criterio de salida:** escenario ambientalmente enriquecido, conservando separada la información real de los elementos procedurales.

## FASE 6 — Optimización

- Caché.
- Sectores.
- LOD.
- Optimización de materiales.
- Carga diferida.
- Gestión de memoria.
- Cancelación.
- Manejo de grandes regiones.

**Criterio de salida:** mejora de rendimiento respaldada por mediciones comparables.

## FASE 7 — Exportación avanzada

- GLB configurable.
- Metadatos.
- Atribuciones.
- Paquetes ZIP.
- Validación con Blender.
- Validación con Godot 4.

**Criterio de salida:** modelos importables con dimensiones, materiales y estructura adecuados.

## FASE 8 — Estabilización

- Pruebas de regresión.
- Manejo de errores.
- Scripts de Windows.
- Documentación.
- Revisión de licencias.
- Corrección de fallos.
- Limpieza de código.

**Criterio de salida:** instalación y ejecución reproducibles en el entorno disponible.

# 28. PRUEBAS GEOGRÁFICAS REALES

Realiza pruebas con al menos las siguientes clases de regiones.

## Caso A — Sangolquí, Ecuador

Área urbana cercana a la Universidad de las Fuerzas Armadas ESPE.

Objetivos:

- Consultar Overture.
- Consultar OSM.
- Comparar edificios.
- Detectar duplicados.
- Generar carreteras.
- Incorporar elevación.
- Exportar GLB.

Utiliza coordenadas obtenidas de una fuente geográfica verificable.

No inventes coordenadas de prueba.

## Caso B — Ciudad con alta densidad de edificios

Selecciona una región donde exista cobertura adecuada de edificios con diferentes alturas.

Valida:

- Geometrías complejas.
- Edificios parciales.
- Alturas.
- Rendimiento.
- Exportación.

## Caso C — Zona rural de Ecuador

Valida:

- Edificios dispersos.
- Carreteras.
- Terreno.
- Vegetación.
- Carencia de atributos.

## Caso D — Región montañosa

Valida:

- Elevación.
- Pendientes.
- Nivelación de edificios.
- Superposición de vías.
- Precisión vertical.

## Caso E — Información geográfica limitada

Selecciona una región con pocos datos OSM.

Comprueba si Overture u otra fuente realmente aporta información adicional.

Documenta resultados antes y después de la integración.

## Caso F — Sin datos disponibles

La aplicación debe responder correctamente.

No debe crear construcciones ficticias.

Debe mostrar un mensaje explicativo.

## Caso G — Fallos de fuentes

Simula:

- Overpass sin respuesta.
- Overture temporalmente inaccesible.
- DEM no disponible.
- Archivos corruptos.
- Datos conflictivos.
- Conversión fallida.
- Cancelación de trabajo.

El sistema debe conservar los resultados válidos y comunicar qué partes no pudieron completarse.

# 29. PRUEBAS AUTOMATIZADAS Y VALIDACIÓN

Implementa pruebas unitarias, de integración y end-to-end.

Verifica:

- Proyecciones.
- Transformación de coordenadas.
- Distancias.
- Elevaciones.
- Reproyección de raster.
- Reparación de geometrías.
- Multipolígonos.
- Detección de duplicados.
- Edificios adyacentes.
- Edificios con patios.
- Partes de edificios.
- Prioridad de alturas.
- Procedencia de atributos.
- Compatibilidad de fuentes.
- Validación de licencias.
- Caché.
- Exportación.
- Tamaño y estructura de GLB.
- Lectura de metadatos.
- Errores de proveedores.

Utiliza fixtures de datos geográficos pequeños, deterministas y almacenables en el repositorio.

Separa las pruebas que requieren Internet de las pruebas completamente locales.

No dependas exclusivamente de solicitudes a servicios externos para ejecutar la batería de pruebas.

Para cada prueba reporta:

- Resultado.
- Fuente de datos.
- Parámetros.
- Método.
- Evidencia.
- Error encontrado, si existe.

No inventes resultados.

# 30. EJECUCIÓN EN WINDOWS

El proyecto debe funcionar en Windows 10/11.

Genera scripts PowerShell para:

- Verificar Node.js.
- Verificar Python.
- Verificar Java.
- Verificar OSM2World.
- Instalar dependencias.
- Crear entorno virtual.
- Preparar configuración.
- Iniciar backend.
- Iniciar frontend.
- Comprobar servicios.
- Ejecutar pruebas.

No exijas Docker o WSL.

Pueden incluirse como alternativas, pero no deben ser requisitos del desarrollo local.

Evita modificar las políticas de seguridad globales de PowerShell.

Ofrece instrucciones para resolver errores comunes.

No presupongas que todos los usuarios tienen las mismas rutas de instalación.

Las rutas deben configurarse mediante variables de entorno.

# 31. CONTROL DE VERSIONES

Si existe un repositorio Git:

- Inspecciona su estado antes de modificarlo.
- Conserva los cambios existentes.
- No elimines código del usuario sin justificación.
- Crea commits coherentes.
- Documenta cada fase.
- No subas archivos pesados innecesariamente.
- No subas credenciales.
- No sobrescribas ramas remotas sin autorización.

Si no existe un repositorio, inicializa uno local.

Si tienes acceso a GitHub y el usuario ha proporcionado un repositorio de destino autorizado, puedes utilizarlo conforme a los permisos disponibles.

No reutilices automáticamente repositorios ajenos o pertenecientes a otros proyectos.

# 32. DOCUMENTACIÓN TÉCNICA

Genera documentación detallada de:

- Arquitectura.
- Instalación.
- Dependencias.
- API.
- Proveedores.
- Normalización.
- Fusión de edificios.
- Georreferenciación.
- Manejo de alturas.
- Integración DEM.
- Generación de escenas.
- Exportación.
- Licencias.
- Optimización.
- Limitaciones.
- Pruebas.
- Solución de problemas.

Explica cómo agregar un nuevo proveedor geográfico sin modificar todo el sistema.

Incluye instrucciones para importar un GLB en Blender y Godot 4.

Documenta las unidades y ejes esperados.

# 33. CRITERIOS FINALES DE ACEPTACIÓN

El proyecto se considerará completo cuando permita realizar el siguiente flujo:

1. Abrir City3D Engine.
2. Introducir una ubicación real.
3. Seleccionar una región.
4. Consultar Overture y OSM.
5. Evaluar cobertura.
6. Consultar una fuente secundaria cuando aporte información.
7. Unificar edificios.
8. Eliminar duplicados correctamente.
9. Incorporar alturas reales o estimadas con procedencia.
10. Generar una escena tridimensional.
11. Incorporar un DEM cuando exista.
12. Visualizar edificios, carreteras y terreno.
13. Navegar libremente.
14. Consultar las propiedades de un edificio.
15. Visualizar fuentes y calidad.
16. Cambiar la apariencia del escenario.
17. Exportar GLB.
18. Descargar metadatos y atribuciones.
19. Importar el modelo en Blender o Godot.
20. Reabrir un escenario previamente generado.

Todo lo anterior debe tener evidencia de funcionamiento.

No declares terminada una funcionalidad sin haberla probado.

# 34. REQUISITOS DE ENTREGA

Entrega:

- Código fuente completo.
- Frontend.
- Backend.
- Adaptadores de datos implementados.
- Motor de fusión.
- Módulo de calidad.
- Generador tridimensional.
- Sistema de terreno.
- Visor 3D.
- Exportación GLB.
- Metadatos y atribuciones.
- Scripts Windows.
- README.
- Documentación.
- Pruebas automatizadas.
- Evidencia de resultados reales.
- Lista de limitaciones.
- Lista de funcionalidades pendientes, si las hubiera.

Incluye, como mínimo, un ejemplo real de escenario GLB generado a partir de información geográfica válida, siempre que el entorno permita completar esa generación.

Si una prueba no puede ejecutarse por limitaciones del entorno, informa de ello y entrega el código verificable disponible.

# 35. INSTRUCCIONES OPERATIVAS DEL AGENTE

Trabaja de manera autónoma y sistemática.

No respondas únicamente con una propuesta o explicación.

Debes crear y modificar archivos, desarrollar código y ejecutar las pruebas que estén a tu alcance.

Antes de implementar componentes grandes, confirma que las dependencias y formatos funcionan mediante pruebas pequeñas.

Prioriza primero un flujo completo y funcional.

Después mejora progresivamente cobertura, calidad, relieve, interfaz y rendimiento.

No intentes resolver todos los aspectos simultáneamente si eso impide obtener una primera versión ejecutable.

No introduzcas simulaciones engañosas.

Puedes utilizar datos de prueba para validar componentes internos, pero el resultado final debe poder trabajar con datos reales.

No ocultes errores con datos ficticios.

Si una biblioteca o herramienta presenta incompatibilidades, investiga alternativas gratuitas, documenta la decisión y utiliza la que ofrezca mayor estabilidad.

Mantén los módulos desacoplados para poder sustituir proveedores.

No solicites autorización para decisiones técnicas menores, seguras y reversibles.

No realices acciones destructivas ni publiques archivos en destinos remotos no autorizados.

Cuando una tarea no pueda completarse, entrega el avance funcional, las pruebas disponibles y una explicación concreta del impedimento.

# 36. ORDEN DE EJECUCIÓN INMEDIATO

Empieza ahora.

**Primera acción:**

Inspecciona el entorno de desarrollo y el proyecto disponible.

Si se proporciona un prototipo anterior llamado `city3d-starter`, revísalo y reutiliza sus componentes funcionales.

**Segunda acción:**

Investiga los repositorios de referencia y verifica la CLI actual de OSM2World.

**Tercera acción:**

Realiza una prueba técnica mínima:

Coordenadas reales → datos geográficos → geometría 3D → GLB.

**Cuarta acción:**

Implementa la interfaz web conectada al backend.

**Quinta acción:**

Integra Overture Maps como fuente consolidada principal de edificios.

**Sexta acción:**

Integra OSM como fuente cartográfica y de enriquecimiento.

**Séptima acción:**

Construye el motor de fusión y trazabilidad.

**Octava acción:**

Añade elevación real y ajuste del terreno.

**Novena acción:**

Integra los proveedores complementarios solo cuando aporten beneficios verificables y legalmente compatibles.

**Décima acción:**

Optimiza, ejecuta pruebas y documenta.

No te detengas tras producir un análisis inicial cuando el entorno permita continuar programando.

---

# RESULTADO FINAL ESPERADO

**City3D Engine debe convertirse en una plataforma GIS 3D gratuita, modular, extensible y técnicamente verificable que transforme información geográfica real proveniente de varias fuentes abiertas en escenarios tridimensionales navegables y exportables.**

El resultado debe poder representar edificios, carreteras, terrenos y elementos ambientales, respetando la precisión y las limitaciones de los datos originales.

Debe funcionar en zonas con información OpenStreetMap abundante y también aprovechar fuentes alternativas cuando OSM tenga cobertura insuficiente.

La arquitectura debe permitir introducir nuevas bases de datos geográficas en el futuro sin reescribir el generador 3D.

**Prioridades finales, en orden:**

1. Funcionamiento real.
2. Precisión geográfica.
3. Calidad y procedencia de los datos.
4. Compatibilidad de licencias.
5. Exportación correcta.
6. Rendimiento.
7. Facilidad de uso.
8. Apariencia visual.

**Construye el proyecto. Ejecuta pruebas. Corrige errores. Verifica los modelos generados. Documenta las decisiones y entrega una aplicación funcional.**
