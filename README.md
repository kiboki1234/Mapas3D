# City3D Engine

City3D Engine transforma datos geográficos abiertos de una región pequeña en una escena 3D navegable y exportable. Consulta OpenStreetMap y Overture Maps, incorpora elevaciones Copernicus/Terrarium o GeoTIFF locales y clasificación ESA WorldCover, normaliza edificios y vías, conserva la procedencia por atributo y genera un archivo GLB con dimensiones métricas.

Esta entrega es un **MVP vertical verificable**, no una reconstrucción fotorealista. El relieve procede de datos DEM reales. Cuando no existe altura ni número de pisos, el edificio se conserva únicamente como huella y no se inventa un volumen.

### Precisión y datos locales (0.4)

- Selector de relieve automático, Copernicus GLO-30, Terrarium o GeoTIFF local.
- Importación gráfica de edificios GeoJSON y elevaciones DTM/DSM, con fecha, licencia, atribución, unidades y datum declarados.
- Clasificación ESA WorldCover 2021 opcional sobre el relieve; los colores no son fotografías.
- Fusión mediante índice espacial, prioridad geométrica local y protección de alturas explícitas frente a predicciones.
- Inspector con fuente de altura y fecha local; las alturas estimadas se distinguen de las derivadas por pisos.
- Resolución del dato original separada de la densidad de la malla. Copernicus es DSM, no terreno desnudo.

Consulte [la guía de precisión e importación](docs/precision-workflow.md) para los formatos, límites y funcionalidades todavía pendientes.

## Flujo implementado

1. Buscar un lugar o introducir latitud/longitud.
2. Elegir un radio seguro entre 100 y 1.000 metros, o dibujar un rectángulo en el mapa.
3. Seleccionar Overture y/o OpenStreetMap.
4. Crear un trabajo persistente y cancelable.
5. Descargar y cachear los datos por región y proveedor.
6. Proyectar WGS84 a la zona UTM local apropiada.
7. Detectar duplicados con identificadores, IoU, áreas y distancia entre centroides.
8. Resolver alturas explícitas, derivadas de pisos o conservar solo la huella.
9. Descargar y muestrear elevaciones DEM; ajustar terreno, edificios y vías.
10. Generar mallas de edificios, carreteras y relieve.
11. Visualizar, inspeccionar y descargar GLB, metadatos y atribuciones.

## Estado real de las fases

| Fase | Estado | Evidencia |
|---|---|---|
| 0 · Investigación | Parcial completada | Arquitectura, riesgos, OSM2World/Overture auditados |
| 1 · Generador mínimo | Implementada | React + FastAPI + OSM + visor + GLB |
| 2 · Overture y fusión | Implementada para edificios | Cliente oficial, GERS, procedencia, fusión inicial |
| 3 · Fuentes complementarias | Parcial | GeoJSON local; Microsoft/Google directos y TEMPO siguen pendientes |
| 4 · Relieve | Implementada para GeoTIFF y fuentes globales | Copernicus, Terrarium, GeoTIFF DTM/DSM, unidades, NoData, datum y resolución |
| 5 · Ambientación | Clasificación implementada | ESA WorldCover 2021 opcional; sin árboles ficticios ni fotografía |
| 6 · Optimización | Parcial | Caché y límites; faltan sectores/LOD avanzado |
| 7 · Exportación | Parcial | GLB + JSON + atribuciones; falta ZIP/Blender/Godot automatizado |
| 8 · Estabilización | En curso | Pruebas locales y scripts Windows disponibles |

## Requisitos

- Windows 10 u 11 con PowerShell.
- Python 3.11 o superior.
- Node.js 20 o superior y npm.
- Acceso a Internet para Overture, Overpass, Nominatim, teselas del mapa y DEM Terrarium.
- Java solo será obligatorio cuando se active el adaptador opcional de OSM2World.

No requiere Docker, WSL, tarjeta bancaria ni API comercial.

## Instalación reproducible en Windows

```powershell
cd D:\mapas3d
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup-windows.ps1
.\scripts\start-dev.ps1
```

La recarga automática es opcional (`.\scripts\start-dev.ps1 -Reload`). En algunas instalaciones de Miniconda para Windows el modo estable sin recarga evita errores al crear subprocesos.

Abra:

- Interfaz: <http://127.0.0.1:5173>
- API/OpenAPI: <http://127.0.0.1:8000/docs>
- Salud: <http://127.0.0.1:8000/api/health>

Para detener los procesos iniciados por el script:

```powershell
.\scripts\stop-dev.ps1
```

## Prueba manual mínima

La interfaz parte de las coordenadas documentadas del campus matriz de la Universidad de las Fuerzas Armadas ESPE en Sangolquí: `-0.314861, -78.443472`.

1. Mantenga un radio de 250 m.
2. Active OSM; active Overture si aparece disponible.
3. Mantenga activo **Relieve DEM** para incorporar las elevaciones reales.
4. En **Modelo 3D**, ajuste únicamente la conversión de pisos observados si es necesario.
5. Pulse **Generar escenario**.
6. Observe el progreso inferior hasta `Completado`.
7. Cambie a **Escena 3D**, seleccione un edificio y revise fuente, altura y cota DEM.
8. Descargue el modelo GLB y `metadata.json`.

Si una fuente falla, el trabajo continúa con las restantes. Si ninguna devuelve datos, el sistema informa el fallo y no crea construcciones ficticias.

## Pruebas automatizadas

```powershell
.\scripts\run-tests.ps1
```

O manualmente:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest

cd ..\frontend
npm run build
npm run validate:glb -- "D:\ruta\al\modelo.glb"
```

Las pruebas sin Internet validan proyección UTM, dimensiones 20 × 10 m,
normalización OSM, fusión, no fusión de edificios adyacentes, polígonos cóncavos,
patios, multipolígonos, volumen, normales, decodificación Terrarium, relieve, estructura GLB y
contratos de API. `validate:glb` ejecuta además el validador oficial de Khronos.

## Estructura

```text
backend/app/
├── api/             API REST versionada
├── cache/           caché local determinista
├── conflation/      detección de duplicados y fusión
├── data_quality/    métricas reproducibles
├── generation/      escena normalizada y escritor GLB
├── jobs/            persistencia SQLite y ciclo de trabajo
├── licensing/       perfiles y atribuciones
├── models/          contratos y dominio
├── projection/      WGS84 → UTM local
└── providers/       adaptadores independientes

frontend/src/
├── components/
├── features/map/
├── features/viewer/
├── services/
├── stores/
└── types/
```

## API principal

- `GET /api/health`
- `GET /api/capabilities`
- `GET /api/providers`
- `GET /api/search?q=Sangolquí`
- `POST /api/regions/preview`
- `POST /api/datasets/inspect`
- `POST /api/generations`
- `GET /api/generations/{id}`
- `POST /api/generations/{id}/cancel`
- `GET /api/generations/{id}/model`
- `GET /api/generations/{id}/metadata`
- `GET /api/generations/{id}/quality`
- `GET /api/generations/{id}/sources`
- `GET /api/generations/{id}/scene`
- `GET /api/generations/{id}/attributions`

## Precisión y licencias

- WGS84 se usa para intercambio; el procesamiento usa una zona UTM calculada desde el centro.
- En Three.js/GLB: X = este, Y = arriba, Z = sur; unidades = metros.
- OSM y Overture Buildings se tratan como ODbL. El paquete incluye atribuciones y procedencia, pero la documentación no sustituye asesoría legal.
- Un contorno de teledetección puede representar el techo y no la pared exacta.
- No se publica un porcentaje de “cobertura real” si no existe una referencia independiente.

Consulte [arquitectura](docs/architecture.md), [fuentes](docs/data-sources.md), [licencias](docs/licensing.md), [georreferenciación](docs/georeferencing.md), [guía de desarrollo](docs/developer-guide.md), [guía de usuario](docs/user-guide.md) y [validación](docs/validation-report.md).

