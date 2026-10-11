# Georreferenciación

## Convenciones

- Entrada y metadatos geográficos: WGS84 / EPSG:4326, orden longitud-latitud internamente.
- Proyección métrica: UTM calculada desde la longitud y hemisferio del centro.
- Origen local: centro de la selección, restado a eastings/northings.
- GLB/Three.js: X este, Y arriba, Z sur, metros.

La inversión del eje norte a Z sur mantiene un sistema derecho con Y vertical. `metadata.json` registra EPSG, origen geográfico, origen proyectado, unidades y ejes para reconstruir coordenadas. Con DEM, Y representa la diferencia respecto a la elevación del centro; la cota absoluta de referencia se conserva en metadatos.

## Precisión

La prueba determinista crea un polígono de 20 × 10 m en la proyección y exige una tolerancia de 2 cm tras el ciclo geográfico/local. Esto valida la transformación, no la exactitud de la fuente cartográfica.

## Límites

- Una selección no puede cruzar el antimeridiano en el MVP.
- Las áreas cercanas al límite de una zona UTM requieren una proyección local ENU o un CRS regional; el radio máximo reduce este riesgo, pero no lo elimina.
- La cobertura SRTM usa alturas ortométricas referidas al geoide EGM96. Otras fuentes compuestas pueden requerir revisar el datum declarado en sus metadatos.
- La resolución DEM global no equivale a precisión topográfica o catastral.

## Ajuste al relieve (generador 0.3.5)

Las huellas sin altura y las vías se recortan contra los triángulos proyectados del
DEM y se interpolan en sus planos. La interpolación bilineal del raster no coincide
con una malla triangular en celdas no coplanares: usarla para las capas hacía que
atravesaran el relieve. Las capas se elevan 6 cm (huellas) y 3 cm (vías) únicamente
para su separación visual, sin interpretar esos desplazamientos como cotas medidas.
Fuera de la cobertura del DEM estas superficies se recortan, no se extrapolan.

Los edificios con altura se apoyan en la cota máxima bajo su huella. Un zócalo
geométrico cubre el intervalo hasta la cota mínima para evitar bases flotantes o
enterradas. La altura del cuerpo principal se conserva; el zócalo es un ajuste
estimado, separado del edificio y etiquetado en los extras del GLB. Esto no equivale
a un levantamiento de cimentación ni a una nivelación catastral del terreno.

## Blender y Godot 4

Blender: `Archivo → Importar → glTF 2.0`, seleccione el GLB y conserve escala 1.0; una unidad equivale a un metro.

Godot 4: copie el GLB al proyecto, abra la escena importada y mantenga la escala `(1,1,1)`. El eje Y ya es vertical. Use `metadata.json` para reubicar la escena en un contexto geográfico.

