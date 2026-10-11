# Guía de usuario

## Crear una escena

1. Busque una ubicación o escriba coordenadas.
2. Use el círculo o active **Seleccionar rectángulo** y arrastre en el mapa.
3. Elija un radio pequeño; 250 m es el valor recomendado inicial.
4. Active las fuentes disponibles y las carreteras si las necesita.
5. Active **Relieve DEM** para descargar elevación real y ajuste, si lo necesita, la
   conversión aplicada únicamente a edificios con número de pisos observado.
6. Pulse **Generar escenario** y siga el estado inferior.
7. Cuando termine, abra **Escena 3D**.

Puede orbitar con el ratón, usar los botones de vista y seleccionar una malla. Los colores indican altura explícita, derivada o solo huella; cambiar el estilo no descarga datos otra vez.

El estilo inicial **Neutro · geometría** usa una paleta sobria de visualización;
no representa colores observados de las fachadas o del suelo. Los estilos
Cartográfico y GIS permiten ver la clasificación de alturas. En el visor puede
ocultar por separado el relieve, las vías o las huellas sin altura. Esto ayuda a
inspeccionar los volúmenes disponibles sin modificar el GLB exportado.

El panel cuenta las **huellas** y señala cuántas tienen datos para construir volumen
3D. Una huella sin altura no es un edificio de cero metros: es un dato incompleto.
El DEM global no permite deducir las alturas de los techos. Para completar esas
alturas hacen falta fuentes adicionales con atributos de edificio, catastro o
mediciones adecuadas; no se asignan alturas arbitrarias en el modo fiel a fuentes.

## Fidelidad del modelo

- Los contornos de edificios y vías proceden de las fuentes seleccionadas.
- El ancho vial conserva `width` cuando existe; de lo contrario se deriva de la clase `highway` y queda marcado como estimado.
- Los colores son una leyenda de calidad; no simulan materiales observados.
- Una altura explícita se conserva. Una altura derivada usa pisos observados y la conversión indicada.
- Sin altura ni pisos, se exporta únicamente la huella sobre el terreno.
- El DEM se decodifica en metros y conserva cota absoluta, datum, resolución y proveedor en metadatos.

Los patios de los polígonos se conservan abiertos y las normales se exportan para que la
iluminación funcione de forma coherente en otros motores.

## Exportar

- GLB: terreno, edificios y carreteras en metros.
- Metadatos JSON: origen, CRS, fuentes, calidad, decisiones de fusión y mapeo de objetos.
- Atribuciones: créditos y enlaces de licencia.

## Mensajes importantes

- “Solo huella” significa que existe un contorno observado, pero no una altura verificable.
- “Cobertura observada” cuenta lo devuelto por proveedores; no afirma cuántos edificios existen realmente.
- “Terreno plano” aparece únicamente si el usuario desactiva el DEM.
- “Cubiertas planas” significa que todavía no se generaron tejados inclinados.
- Si Overture falla, OSM puede completar la generación y el fallo queda registrado.
- Una escena con fuentes fallidas no se reutiliza automáticamente desde caché al
  pulsar Generar; se vuelven a consultar. La consulta Overture usa el índice espacial
  STAC del SDK oficial y un proceso con límite de 120 segundos. Los fallos del SDK
  no se guardan como si fueran cobertura vacía.

