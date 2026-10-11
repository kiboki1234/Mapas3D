# Informe de validación

Fecha de la primera validación local: 2026-10-10, zona America/Guayaquil.

## Entorno observado

- Windows / PowerShell 7.
- Node.js 25.2.1 y npm 11.6.2.
- Python 3.13.12 mediante Miniconda; entorno virtual aislado creado.
- Java 25.0.1 disponible.
- OSM2World no encontrado en PATH ni configurado.

## Pruebas locales sin Internet

- Selección de EPSG:32717 para Sangolquí.
- Conservación de un rectángulo 20 × 10 m con tolerancia de 2 cm.
- Bounding box geodésico contiene su centro.
- Dos representaciones superpuestas se fusionan y OSM completa altura.
- Edificios que solo comparten pared no se fusionan.
- Fixture OSM produce un edificio y una carretera.
- La respuesta de respaldo de OSM Map API reconstruye nodos y geometrías de vías.
- GLB contiene cabecera glTF 2.0, dos mallas y dos nodos.
- `/api/health`, `/api/providers` y `/api/regions/preview` cumplen contrato.

Resultado registrado originalmente: 10 pruebas superadas.

## Validación del generador 0.2

- 20 pruebas automáticas superadas.
- Contornos horarios y antihorarios conservan el mismo volumen.
- Polígonos cóncavos, multipolígonos y polígonos con dos patios conservan área,
  volumen y bordes cerrados.
- El GLB exporta normales unitarias coherentes, UV métricas e índices compactos.
- El validador detecta índices fuera de rango, triángulos degenerados, normales inválidas,
  accesores fuera del buffer y escenas sin mallas.
- Generación real con acabado procedural: 36 edificios, 106 vías, 142 mallas,
  2.134 triángulos y tres texturas PNG incrustadas; tamaño 287.996 bytes.
- Khronos glTF Validator: cero errores y cero advertencias. Se reportó únicamente una
  observación informativa por un material de altura no utilizado en esta región.
- El visor abrió el GLB generado, mostró el estilo Arquitectónico y no registró errores
  ni advertencias en la consola.

## Validación del generador 0.3.3 con DEM real

- Tesela Terrarium real descargada para Sangolquí, zoom 12.
- Cuadrícula DEM: 33 × 33; resolución aproximada de píxel: 38,22 m.
- Cotas observadas en la selección: 2.488,518–2.513,325 m; referencia central: 2.499,637 m.
- Escenario real: 36 huellas de edificios, 106 vías y una malla DEM; 143 mallas GLB.
- GLB final: 3.562 triángulos, 10.257 vértices de primitivas y 412.184 bytes.
- Alturas disponibles: una derivada de pisos observados y 35 edificios conservados solo
  como huella. No se generaron volúmenes de altura desconocida.
- Anchos viales: 7 observados y 99 derivados de la clase `highway`; ambos grupos quedan
  diferenciados en calidad, escena y `extras` del GLB.
- El trabajo finalizó sin error y conservó fuente, zoom, resolución, datum y cotas en JSON/GLB.
- El validador Khronos reportó cero errores y cero advertencias.

## Validación real de extremo a extremo

- Región: campus ESPE, Sangolquí (`-0.314861, -78.443472`), radio de 250 m.
- Fuente efectiva: OpenStreetMap, con respaldo automático desde Overpass hacia OSM Map API.
- Resultado: 36 edificios, 106 vías y 142 mallas.
- Artefacto GLB: 191.460 bytes; metadatos, informe de calidad, escena y atribuciones generados.
- La interfaz cargó el GLB, mostró las métricas y aceptó de nuevo el mismo trabajo desde caché.
- No aparecieron errores o advertencias nuevos en la consola después de corregir el cargador 3D.

## Validación pendiente de red y aplicaciones externas

- Consulta real simultánea Overture + OSM en Sangolquí (la prueba actual completó con OSM; el catálogo remoto de Overture no respondió en este entorno).
- Apertura del GLB generado con datos reales en Blender y Godot 4.
- Casos de zona urbana densa, rural, montaña, datos escasos, sin datos y fallos inducidos.
- Medición comparable de rendimiento y memoria.

Estas validaciones no se declaran completadas hasta conservar evidencia de ejecución.

