from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.domain import ProviderResult
from app.models.schemas import BoundingBox, ProviderInfo


class GeospatialProvider(ABC):
    id: str

    @abstractmethod
    def info(self) -> ProviderInfo:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, bbox: BoundingBox, include_roads: bool = True) -> ProviderResult:
        raise NotImplementedError

