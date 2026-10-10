from __future__ import annotations

from app.cache.service import FileCache
from app.core.config import Settings
from app.providers.base import GeospatialProvider
from app.providers.osm import OpenStreetMapProvider
from app.providers.overture import OvertureProvider


def build_provider_registry(settings: Settings) -> dict[str, GeospatialProvider]:
    cache = FileCache(settings.cache_dir / "providers")
    return {
        "overture": OvertureProvider(cache),
        "osm": OpenStreetMapProvider(settings, cache),
    }

