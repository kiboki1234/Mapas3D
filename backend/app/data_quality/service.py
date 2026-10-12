from __future__ import annotations

from collections import Counter
from typing import Any

from app.models.domain import FusedDataset, ProviderResult, TerrainGrid


def analyze_quality(
    results: list[ProviderResult], fused: FusedDataset, terrain: TerrainGrid | None = None
) -> dict[str, Any]:
    source_counts = Counter(building.provider for result in results for building in result.buildings)
    height_types = Counter(
        str(building.attributes.get("height_type").value)
        for building in fused.buildings
        if building.attributes.get("height_type")
    )
    total = len(fused.buildings)
    invalid = sum(
        1 for building in fused.buildings if building.validation_status not in {"valid", "repaired"}
    )
    warnings = list(fused.warnings)
    footprints = height_types.get("footprint_only", 0)
    if footprints:
        warnings.append(
            f"{footprints} de {total} edificios no tienen altura ni pisos en las fuentes consultadas. "
            "Se conservan sus huellas; el DEM no proporciona la altura de los edificios."
        )
    if not total:
        warnings.append(
            "Ningún proveedor devolvió edificios para esta región; no se generaron construcciones ficticias."
        )
    return {
        "definitions": {
            "observed_source_count": "Elementos devueltos por cada fuente antes de la fusión.",
            "unique_buildings": "Edificios conservados después de resolver duplicados espaciales.",
            "attribute_completeness": "Fracción de edificios únicos con un atributo disponible.",
            "not_ground_truth": (
                "Estas métricas describen los datos obtenidos; no estiman el porcentaje real de "
                "edificios existentes en el territorio."
            ),
            "explicit_height": "Atributo height declarado por una fuente; no implica medición topográfica certificada.",
            "confidence": "No se asignan probabilidades de precisión sin una calibración o puntuación publicada por la fuente.",
        },
        "raw_buildings": sum(source_counts.values()),
        "unique_buildings": total,
        "buildings_by_source_before_fusion": dict(source_counts),
        "duplicates_merged": len(fused.fusion_decisions),
        "conflicts": sum(len(building.conflicts) for building in fused.buildings),
        "invalid_geometries": invalid,
        "roads": len(fused.roads),
        "road_width": {
            "observed": sum(not road.width_estimated for road in fused.roads),
            "derived_from_class": sum(road.width_estimated for road in fused.roads),
        },
        "height": {
            "explicit": height_types.get("explicit", 0),
            "derived_from_floors": height_types.get("derived", 0),
            "estimated_spatial": height_types.get("estimated", 0),
            "unknown_visual_default": height_types.get("unknown", 0),
            "footprint_only": height_types.get("footprint_only", 0),
            "explicit_percent": round(height_types.get("explicit", 0) * 100 / total, 1)
            if total
            else 0,
        },
        "terrain": {
            "available": terrain is not None,
            "mode": "dem" if terrain is not None else "flat",
            "coverage": 1.0 if terrain is not None else None,
            "provider": terrain.source.get("provider") if terrain else None,
            "dataset": terrain.source.get("dataset") if terrain else None,
            "surface_type": terrain.source.get("surface_type", "mixed DEM") if terrain else None,
            "vertical_datum": terrain.source.get("vertical_datum") if terrain else None,
            "output_grid_spacing_m": terrain.source.get("output_grid_spacing_m") if terrain else None,
            "elevation_min_m": terrain.source.get("elevation_min_m") if terrain else None,
            "elevation_max_m": terrain.source.get("elevation_max_m") if terrain else None,
            "reference_elevation_m": (
                terrain.source.get("reference_elevation_m") if terrain else None
            ),
            "pixel_resolution_m": terrain.source.get("pixel_resolution_m") if terrain else None,
        },
        "landcover": terrain.landcover_source if terrain else None,
        "imagery": terrain.imagery_source if terrain else None,
        "vegetation": {"available": False, "mode": "no individual trees generated"},
        "warnings": warnings,
    }

