# Arquitectura

## Decisión principal

City3D Engine comienza como monolito modular: una SPA React y una API FastAPI con módulos internos. No hay microservicios, Redis, colas externas ni Kubernetes porque un MVP local no los justifica. Las fronteras de los módulos permiten extraer un worker o proveedor si aparecen carga y equipos independientes.

```text
React/Leaflet/Three.js
        │ REST
        ▼
FastAPI ── Jobs SQLite
  │
  ├── Provider Registry ── Overture / OSM
  ├── Projection ── WGS84 → UTM local
  ├── Fusion ── IDs + IoU + área + centroides
  ├── Quality ── métricas observadas
  ├── Generation ── mallas métricas + GLB
  └── Licensing ── procedencia + atribuciones
```

## Reglas de dependencia

- `api` coordina casos de uso; no contiene algoritmos GIS.
- `providers` traduce fuentes externas a objetos de dominio.
- `conflation` solo conoce objetos normalizados, no HTTP ni archivos externos.
- `generation` recibe el conjunto fusionado y no consulta proveedores.
- `licensing` bloquea perfiles incompatibles antes de descargar/generar.
- `jobs` registra estados y artefactos, y permite cancelación en puntos seguros.

## Contrato de proveedor

Cada adaptador implementa `GeospatialProvider.info()` y `fetch(bbox, include_roads)`. Debe devolver edificios y vías normalizados, registro de fuente, licencia y advertencias. Un proveedor nuevo se registra en `app/providers/registry.py`; no necesita modificar el motor 3D.

## Registro de decisiones técnicas

### ADR-001 — Generador geométrico propio en el MVP

OSM2World no está instalado en el entorno auditado. Además, los datos fusionados de Overture/OSM no son entrada OSM nativa. Se eligió un escritor GLB propio para volúmenes LOD0 y carreteras, con OSM2World reservado como adaptador opcional. Esto evita fabricar XML OSM inválido y mantiene el flujo completo verificable.

### ADR-002 — UTM local por trabajo

Se eliminan factores arbitrarios como el `51000` observado en `map3d`. La zona UTM se calcula desde el centro; en Sangolquí corresponde EPSG:32717. El origen local reduce errores de precisión de `float32` en WebGL/glTF.

### ADR-003 — Overture antes que OSM para geometría

Overture es la fuente consolidada inicial. OSM puede enriquecer altura, pisos y nombre. La geometría Overture se conserva cuando el emparejamiento es concluyente; cada decisión queda registrada. La prioridad se hará más configurable al integrar fuentes oficiales.

### ADR-004 — SQLite y tareas locales

SQLite basta para persistir estados en una máquina. `BackgroundTasks` ejecuta el trabajo fuera de la respuesta HTTP. Antes de producción multiusuario se debe migrar el procesamiento a un worker duradero con límites de CPU/memoria.

## Riesgos conocidos

- La fusión inicial no modela todavía edificios con partes de forma jerárquica.
- El algoritmo O(n²) está limitado por el radio máximo; regiones extensas requieren índice espacial y sectores.
- El generador no crea tejados inclinados ni DEM.
- Overpass público no ofrece SLA y debe reemplazarse por extractos para uso sostenido.
- La triangulación GLB debe validarse con más polígonos complejos antes de producción.

