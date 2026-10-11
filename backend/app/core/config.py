from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="CITY3D_",
        extra="ignore",
    )

    app_name: str = "City3D Engine API"
    environment: str = "development"
    api_prefix: str = "/api"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    data_dir: Path = PROJECT_ROOT / "data"
    max_radius_m: int = Field(default=1000, ge=100, le=5000)
    default_floor_height_m: float = Field(default=3.0, ge=2.0, le=6.0)
    unknown_building_height_m: float = Field(default=6.0, ge=2.0, le=30.0)
    overpass_endpoints: str = (
        "https://overpass-api.de/api/interpreter,"
        "https://overpass.kumi.systems/api/interpreter"
    )
    http_timeout_seconds: int = Field(default=45, ge=5, le=180)
    user_agent: str = "City3D-Engine/0.1 (local open-source GIS prototype)"
    nominatim_endpoint: str = "https://nominatim.openstreetmap.org/search"
    osm_map_endpoint: str = "https://api.openstreetmap.org/api/0.6/map.json"
    terrain_tile_endpoint: str = (
        "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
    )
    terrain_zoom: int = Field(default=12, ge=0, le=15)

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]

    @property
    def overpass_urls(self) -> list[str]:
        return [item.strip() for item in self.overpass_endpoints.split(",") if item.strip()]

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated"

    @property
    def dem_cache_dir(self) -> Path:
        return self.data_dir / "dem"

    @property
    def jobs_database(self) -> Path:
        return self.data_dir / "city3d.sqlite3"

    def ensure_directories(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.dem_cache_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

