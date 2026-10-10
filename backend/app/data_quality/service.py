from __future__ import annotations

from collections import Counter
from typing import Any

from app.models.domain import FusedDataset, ProviderResult


def analyze_quality(results: list[ProviderResult], fused: FusedDataset) -> dict[str, Any]:
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
        },
        "raw_buildings": sum(source_counts.values()),
        "unique_buildings": total,
        "buildings_by_source_before_fusion": dict(source_counts),
        "duplicates_merged": len(fused.fusion_decisions),
        "conflicts": sum(len(building.conflicts) for building in fused.buildings),
        "invalid_geometries": invalid,
        "roads": len(fused.roads),
        "height": {
            "explicit": height_types.get("explicit", 0),
            "derived_from_floors": height_types.get("derived", 0),
            "estimated_spatial": height_types.get("estimated", 0),
            "unknown_visual_default": height_types.get("unknown", 0),
            "explicit_percent": round(height_types.get("explicit", 0) * 100 / total, 1)
            if total
            else 0,
        },
        "terrain": {"available": False, "mode": "flat", "coverage": None},
        "vegetation": {"available": False, "mode": "disabled"},
        "warnings": warnings,
    }

