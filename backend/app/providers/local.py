from __future__ import annotations

import json

from shapely.geometry import box, shape

from app.datasets.store import DatasetStore
from app.models.domain import AttributeValue, Building, ProviderResult
from app.models.schemas import BoundingBox


def fetch_local_buildings(store: DatasetStore, dataset_id: str, bbox: BoundingBox) -> ProviderResult:
    record = store.get(dataset_id)
    if record["kind"] != "buildings":
        raise ValueError("El dataset seleccionado no contiene edificios")
    source_id = f"local:{dataset_id}"
    region = box(*bbox.as_tuple())
    buildings = []
    collection = json.loads(store.data_path(dataset_id).read_text(encoding="utf-8-sig"))
    for index, feature in enumerate(collection["features"]):
        geometry = shape(feature["geometry"])
        if not region.intersects(geometry):
            continue
        # Preserve the complete footprint, avoiding false walls from clipping.
        props = feature.get("properties") or {}
        attributes = {}
        for key, source_key in (("height", "height_m"), ("num_floors", "num_floors"), ("name", "name")):
            if props.get(source_key) is not None:
                attributes[key] = AttributeValue(props[source_key], source_id,
                    estimated=bool(key == "height" and props.get("height_estimated", False)))
        if "height" in attributes:
            attributes["height_type"] = AttributeValue(
                "estimated" if attributes["height"].estimated else "explicit", source_id)
        attributes["source_date"] = AttributeValue(record["source_date"], source_id)
        original_id = str(feature.get("id", index))
        buildings.append(Building(
            id=f"{source_id}:{index}", geometry=geometry, provider=source_id,
            original_ids={source_id: original_id}, attributes=attributes,
            license=record["license"], source_records=[{"dataset": record["name"],
                "record_id": original_id, "source_date": record["source_date"],
                "sha256": record["sha256"], "provenance_status": record["provenance_status"]}],
        ))
    return ProviderResult(source_id, buildings, [], {
        **record, "provider": source_id, "dataset": record["name"],
        "raw_feature_count": len(buildings),
    }, ["Datos locales: procedencia, fecha y licencia declaradas por el usuario; no certificadas."])
