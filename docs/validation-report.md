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

Resultado registrado: 10 pruebas superadas.

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

