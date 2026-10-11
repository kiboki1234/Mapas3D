from __future__ import annotations

from dataclasses import dataclass

from pyproj import CRS, Geod, Transformer
from shapely import transform
from shapely.affinity import translate
from shapely.geometry.base import BaseGeometry

from app.models.schemas import BoundingBox


WGS84 = CRS.from_epsg(4326)
GEOD = Geod(ellps="WGS84")


def bounding_box_from_center(latitude: float, longitude: float, radius_m: float) -> BoundingBox:
    west_lon, _, _ = GEOD.fwd(longitude, latitude, 270, radius_m)
    east_lon, _, _ = GEOD.fwd(longitude, latitude, 90, radius_m)
    _, south_lat, _ = GEOD.fwd(longitude, latitude, 180, radius_m)
    _, north_lat, _ = GEOD.fwd(longitude, latitude, 0, radius_m)
    return BoundingBox(west=west_lon, south=south_lat, east=east_lon, north=north_lat)


def utm_epsg_for(latitude: float, longitude: float) -> int:
    zone = max(1, min(60, int((longitude + 180) / 6) + 1))
    return (32600 if latitude >= 0 else 32700) + zone


@dataclass(slots=True)
class LocalProjection:
    latitude: float
    longitude: float
    epsg: int
    origin_easting: float
    origin_northing: float
    transformer: Transformer
    inverse_transformer: Transformer

    @classmethod
    def at(cls, latitude: float, longitude: float) -> "LocalProjection":
        epsg = utm_epsg_for(latitude, longitude)
        transformer = Transformer.from_crs(WGS84, CRS.from_epsg(epsg), always_xy=True)
        inverse_transformer = Transformer.from_crs(
            CRS.from_epsg(epsg), WGS84, always_xy=True
        )
        easting, northing = transformer.transform(longitude, latitude)
        return cls(
            latitude,
            longitude,
            epsg,
            easting,
            northing,
            transformer,
            inverse_transformer,
        )

    def project_geometry(self, geometry: BaseGeometry) -> BaseGeometry:
        projected = transform(geometry, self.transformer.transform, interleaved=False)
        return translate(projected, xoff=-self.origin_easting, yoff=-self.origin_northing)

    def unproject_point(self, x: float, y: float) -> tuple[float, float]:
        longitude, latitude = self.inverse_transformer.transform(
            x + self.origin_easting, y + self.origin_northing
        )
        return float(longitude), float(latitude)

    def metadata(self) -> dict[str, object]:
        return {
            "source_crs": "EPSG:4326",
            "projected_crs": f"EPSG:{self.epsg}",
            "origin": {"latitude": self.latitude, "longitude": self.longitude},
            "origin_projected": {
                "easting": self.origin_easting,
                "northing": self.origin_northing,
            },
            "units": "meters",
            "scene_axes": {"x": "east", "y": "up", "z": "south"},
        }

