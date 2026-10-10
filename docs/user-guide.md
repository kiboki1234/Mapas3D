# Guía de usuario

## Crear una escena

1. Busque una ubicación o escriba coordenadas.
2. Use el círculo o active **Seleccionar rectángulo** y arrastre en el mapa.
3. Elija un radio pequeño; 250 m es el valor recomendado inicial.
4. Active las fuentes disponibles y las carreteras si las necesita.
5. Pulse **Generar escenario** y siga el estado inferior.
6. Cuando termine, abra **Escena 3D**.

Puede orbitar con el ratón, usar los botones de vista y seleccionar una malla. Los colores indican altura explícita, derivada o desconocida; cambiar el estilo no descarga datos otra vez.

## Exportar

- GLB: edificios y carreteras en metros.
- Metadatos JSON: origen, CRS, fuentes, calidad, decisiones de fusión y mapeo de objetos.
- Atribuciones: créditos y enlaces de licencia.

## Mensajes importantes

- “Altura desconocida” significa que el volumen usa 6 m únicamente para ser visible.
- “Cobertura observada” cuenta lo devuelto por proveedores; no afirma cuántos edificios existen realmente.
- “Terreno plano” significa que todavía no se incorporó un DEM.
- Si Overture falla, OSM puede completar la generación y el fallo queda registrado.

