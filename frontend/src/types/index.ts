export type JobStatus =
  | "pending"
  | "downloading"
  | "normalizing"
  | "merging"
  | "processing_terrain"
  | "generating"
  | "validating"
  | "completed"
  | "failed"
  | "cancelled";

export interface GenerationRequest {
  latitude: number;
  longitude: number;
  radius_m: number;
  providers: ("overture" | "osm")[];
  include_buildings: boolean;
  include_roads: boolean;
  include_terrain: boolean;
  material_style?: "plain" | "procedural";
  lod: "lod0" | "lod1";
  floor_height_m: number;
  unknown_height_m: number;
  license_profile: "commercial" | "research";
}

export interface JobEvent {
  timestamp: string;
  level: "info" | "warning" | "error";
  message: string;
}

export interface GenerationJob {
  id: string;
  status: JobStatus;
  progress: number;
  request: GenerationRequest;
  created_at: string;
  updated_at: string;
  error: string | null;
  cancel_requested: boolean;
  cached_from: string | null;
  events: JobEvent[];
  artifacts: Record<string, string>;
}

export interface ProviderInfo {
  id: "overture" | "osm";
  name: string;
  available: boolean;
  enabled_by_default: boolean;
  data_types: string[];
  license: string;
  limitations: string[];
  detail: string | null;
}

export interface QualityReport {
  raw_buildings: number;
  unique_buildings: number;
  buildings_by_source_before_fusion: Record<string, number>;
  duplicates_merged: number;
  conflicts: number;
  invalid_geometries: number;
  roads: number;
  height: {
    explicit: number;
    derived_from_floors: number;
    estimated_spatial: number;
    unknown_visual_default: number;
    explicit_percent: number;
  };
  terrain: { available: boolean; mode: string; coverage: number | null };
  vegetation: { available: boolean; mode: string };
  warnings: string[];
  definitions: Record<string, string>;
}

export interface SearchResult {
  display_name: string;
  latitude: number;
  longitude: number;
  bounding_box: number[];
  category: string | null;
}

export interface SelectedFeature {
  feature_id?: string;
  geometry_source?: string;
  source?: string;
  height_m?: number;
  height_type?: string;
  road_class?: string;
  original_ids?: Record<string, string>;
}

export type ViewerStyle = "cartographic" | "architectural" | "night" | "gis";

