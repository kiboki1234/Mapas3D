# Guía de desarrollo

## Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Agregar un proveedor:

1. Implemente `GeospatialProvider`.
2. Normalice geometrías a WGS84 y objetos `Building`/`Road`.
3. Registre licencia y perfil en `licensing/registry.py`.
4. Añádalo en `providers/registry.py`.
5. Cree fixtures locales y pruebas de error/red.
6. No invoque el proveedor desde el generador o la UI.

## Frontend

```powershell
cd frontend
npm run dev
```

La UI obtiene capacidades del backend. Las rutas se consumen a través de `services/api.ts`; los componentes no codifican URLs de proveedores externos.

## Errores aprendidos

- Un build visual correcto no demuestra que las fuentes, licencias o exportación funcionen.
- Una escala geográfica arbitraria distorsiona dimensiones; proyectar en el backend evita ese defecto.
- Overture puede contener registros derivados de OSM/Microsoft/Google: consultar todo de nuevo produce duplicación y costo sin evidencia.
- Un servicio público puede fallar aunque el código sea correcto; se requiere caché, fallback y mensajes claros.
- La altura visual por defecto nunca debe etiquetarse como medición.
- Sobremuestrear un DEM no crea detalle nuevo; se registra la resolución efectiva de la fuente.
- El relieve debe mover también vías y bases de edificios, no limitarse a una malla decorativa.

## Antes de un commit

```powershell
.\scripts\run-tests.ps1
git status --short
```

No añada `data/generated`, cachés, modelos del usuario, `.env`, credenciales ni el entorno virtual.

