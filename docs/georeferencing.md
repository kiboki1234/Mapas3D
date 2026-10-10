# Georreferenciación

## Convenciones

- Entrada y metadatos geográficos: WGS84 / EPSG:4326, orden longitud-latitud internamente.
- Proyección métrica: UTM calculada desde la longitud y hemisferio del centro.
- Origen local: centro de la selección, restado a eastings/northings.
- GLB/Three.js: X este, Y arriba, Z sur, metros.

La inversión del eje norte a Z sur mantiene un sistema derecho con Y vertical. `metadata.json` registra EPSG, origen geográfico, origen proyectado, unidades y ejes para reconstruir coordenadas.

## Precisión

La prueba determinista crea un polígono de 20 × 10 m en la proyección y exige una tolerancia de 2 cm tras el ciclo geográfico/local. Esto valida la transformación, no la exactitud de la fuente cartográfica.

## Límites

- Una selección no puede cruzar el antimeridiano en el MVP.
- Las áreas cercanas al límite de una zona UTM requieren una proyección local ENU o un CRS regional; el radio máximo reduce este riesgo, pero no lo elimina.
- Todavía no se maneja datum vertical porque el terreno es plano.

## Blender y Godot 4

Blender: `Archivo → Importar → glTF 2.0`, seleccione el GLB y conserve escala 1.0; una unidad equivale a un metro.

Godot 4: copie el GLB al proyecto, abra la escena importada y mantenga la escala `(1,1,1)`. El eje Y ya es vertical. Use `metadata.json` para reubicar la escena en un contexto geográfico.

