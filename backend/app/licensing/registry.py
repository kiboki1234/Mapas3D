from __future__ import annotations

from typing import Any


PROVIDERS: dict[str, dict[str, Any]] = {
    "osm": {
        "name": "OpenStreetMap",
        "dataset": "OpenStreetMap",
        "license": "ODbL-1.0",
        "attribution": "© OpenStreetMap contributors",
        "url": "https://www.openstreetmap.org/copyright",
        "commercial": True,
    },
    "overture": {
        "name": "Overture Maps",
        "dataset": "Overture Buildings",
        "license": "ODbL-1.0",
        "attribution": "© OpenStreetMap contributors, Overture Maps Foundation",
        "url": "https://docs.overturemaps.org/attribution/",
        "commercial": True,
    },
    "mapzen-terrain": {
        "name": "Mapzen Terrain Tiles",
        "dataset": "Terrarium elevation tiles (SRTM and other open DEM sources)",
        "license": "Multiple open datasets",
        "attribution": "Elevation data courtesy of USGS and other Mapzen Terrain sources",
        "url": "https://github.com/tilezen/joerd/blob/master/docs/attribution.md",
        "commercial": True,
    },
}


def provider_license(provider: str) -> dict[str, Any]:
    return PROVIDERS[provider].copy()


def validate_profile(providers: list[str], profile: str) -> list[str]:
    warnings: list[str] = []
    for provider in providers:
        record = PROVIDERS.get(provider)
        if record is None:
            raise ValueError(f"Proveedor sin política de licencia registrada: {provider}")
        if profile == "commercial" and not record["commercial"]:
            raise ValueError(f"{provider} no está habilitado para el perfil comercial")
        if record["license"].startswith("ODbL"):
            warnings.append(
                f"Los datos de {record['name']} están sujetos a ODbL; conserve atribución y revise "
                "las obligaciones aplicables a bases derivadas."
            )
    return warnings


def attribution_text(providers: list[str], include_terrain: bool = False) -> str:
    lines = ["City3D Engine — atribuciones de datos", ""]
    selected = [*providers, *(["mapzen-terrain"] if include_terrain else [])]
    for provider in dict.fromkeys(selected):
        record = PROVIDERS[provider]
        lines.extend(
            [
                record["attribution"],
                f"Dataset: {record['dataset']}",
                f"Licencia: {record['license']}",
                f"Términos: {record['url']}",
                "",
            ]
        )
    lines.append(
        "Este archivo informa la procedencia; no sustituye una revisión legal del uso y redistribución."
    )
    return "\n".join(lines)

