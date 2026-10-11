import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Building2,
  ChevronDown,
  CircleAlert,
  CloudDownload,
  Database,
  Download,
  Layers3,
  LoaderCircle,
  Map as MapIcon,
  MapPin,
  MousePointer2,
  Play,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { SourceBadge } from "./components/SourceBadge";
import { ViewerErrorBoundary } from "./components/ViewerErrorBoundary";
import { GenerationOptions } from "./features/generation/GenerationOptions";
import { api } from "./services/api";
import { AreaMap } from "./features/map/AreaMap";
import { useAppStore } from "./stores/appStore";
import type { GenerationRequest, SearchResult, ViewerStyle } from "./types";

const SceneViewer = lazy(() =>
  import("./features/viewer/SceneViewer").then((module) => ({ default: module.SceneViewer })),
);

const ACTIVE_STATUSES = new Set([
  "pending",
  "downloading",
  "normalizing",
  "merging",
  "processing_terrain",
  "generating",
  "validating",
]);

const statusLabels: Record<string, string> = {
  pending: "En cola",
  downloading: "Descargando fuentes",
  normalizing: "Normalizando",
  merging: "Fusionando",
  processing_terrain: "Procesando terreno",
  generating: "Generando escena",
  validating: "Validando GLB",
  completed: "Completado",
  failed: "Falló",
  cancelled: "Cancelado",
};

export default function App() {
  const {
    job,
    providers,
    quality,
    selectedFeature,
    viewerStyle,
    activeView,
    setJob,
    setProviders,
    setQuality,
    setViewerStyle,
    setActiveView,
  } = useAppStore();
  const [latitude, setLatitude] = useState(-0.314861);
  const [longitude, setLongitude] = useState(-78.443472);
  const [radius, setRadius] = useState(250);
  const [selectedProviders, setSelectedProviders] = useState<("overture" | "osm")[]>(["osm"]);
  const [includeRoads, setIncludeRoads] = useState(true);
  const [selectMode, setSelectMode] = useState(false);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submission = useRef(false);
  const [materialStyle, setMaterialStyle] = useState<"plain" | "procedural">("plain");
  const [floorHeight, setFloorHeight] = useState(3);
  const [unknownHeight, setUnknownHeight] = useState(6);

  useEffect(() => {
    api.providers()
      .then((items) => {
        setProviders(items);
        setSelectedProviders(items.filter((item) => item.available && item.enabled_by_default).map((item) => item.id));
      })
      .catch((reason: Error) => setError(reason.message));
  }, [setProviders]);

  useEffect(() => {
    if (!job || !ACTIVE_STATUSES.has(job.status)) return;
    const id = job.id;
    let cancelled = false;
    let timer: number;
    const poll = async () => {
      try {
        const updated = await api.generation(id);
        if (cancelled) return;
        setPollError(null);
        setJob(updated);
        if (!ACTIVE_STATUSES.has(updated.status)) return;
      } catch (reason) {
        if (cancelled) return;
        setPollError(reason instanceof Error ? reason.message : "No se pudo actualizar el trabajo");
      }
      if (!cancelled) timer = window.setTimeout(() => void poll(), 1600);
    };
    timer = window.setTimeout(() => void poll(), 800);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [job?.id, job?.status, setJob]);

  useEffect(() => {
    if (!job || job.status !== "completed") return;
    let cancelled = false;
    api.quality(job.id)
      .then((report) => {
        if (cancelled) return;
        setQuality(report);
        if (job.request.material_style === "procedural") setViewerStyle("architectural");
        setActiveView("3d");
      })
      .catch((reason: Error) => {
        if (!cancelled) setError(reason.message);
      });
    return () => {
      cancelled = true;
    };
  }, [job?.id, job?.status, setActiveView, setQuality, setViewerStyle]);

  const modelUrl = job?.status === "completed" ? api.artifactUrl(job.id, "model") : null;
  const busy = submitting || ACTIVE_STATUSES.has(job?.status ?? "");
  const canGenerate = selectedProviders.length > 0 && !busy;
  const visibleError = error ?? pollError ?? job?.error;
  const coordinateText = `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;

  const runSearch = async () => {
    if (query.trim().length < 3) return;
    setSearching(true);
    setError(null);
    try {
      setSearchResults(await api.search(query.trim()));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "La búsqueda falló");
    } finally {
      setSearching(false);
    }
  };

  const generate = async () => {
    if (submission.current || !canGenerate) return;
    if (!Number.isFinite(latitude) || Math.abs(latitude) > 90
        || !Number.isFinite(longitude) || Math.abs(longitude) > 180) {
      setError("Ingrese coordenadas válidas: latitud entre -90 y 90 y longitud entre -180 y 180.");
      return;
    }
    const request: GenerationRequest = {
      latitude,
      longitude,
      radius_m: radius,
      providers: selectedProviders,
      include_buildings: true,
      include_roads: includeRoads,
      include_terrain: false,
      material_style: materialStyle,
      lod: "lod0",
      floor_height_m: floorHeight,
      unknown_height_m: unknownHeight,
      license_profile: "commercial",
    };
    setError(null);
    setPollError(null);
    submission.current = true;
    setSubmitting(true);
    try {
      const created = await api.createGeneration(request);
      if (created.id !== job?.id) setQuality(null);
      useAppStore.getState().setSelectedFeature(null);
      setJob(created);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo iniciar la generación");
    } finally {
      submission.current = false;
      setSubmitting(false);
    }
  };

  const cancelGeneration = async () => {
    if (!job) return;
    try { setJob(await api.cancel(job.id)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudo cancelar"); }
  };

  const toggleProvider = (id: "overture" | "osm") => {
    setSelectedProviders((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  };

  const selectSearchResult = (result: SearchResult) => {
    setLatitude(result.latitude);
    setLongitude(result.longitude);
    setSearchResults([]);
    setQuery(result.display_name.split(",")[0]);
  };

  const heightSummary = useMemo(() => {
    if (!quality) return [];
    return [
      ["Explícita", quality.height.explicit, "explicit"],
      ["Derivada", quality.height.derived_from_floors, "derived"],
      ["Desconocida", quality.height.unknown_visual_default, "unknown"],
    ] as const;
  }, [quality]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Layers3 size={22} /></div>
          <div><strong>CITY3D</strong><span>ENGINE</span></div>
          <em>ALPHA</em>
        </div>
        <div className="project-title">
          <small>ESCENARIO ACTUAL</small>
          <span>{query || "Campus ESPE · Sangolquí"}</span>
          <i>{coordinateText}</i>
        </div>
        <div className="top-actions">
          <span className={`api-state ${visibleError ? "error" : ""}`}><i /> {visibleError ? "Atención" : "City3D API"}</span>
          <button className="icon-button" title="Descargar GLB" disabled={!modelUrl} onClick={() => modelUrl && window.open(modelUrl)}>
            <CloudDownload size={18} />
          </button>
        </div>
      </header>

      <section className="workspace">
        <aside className="left-panel panel-scroll">
          <div className="panel-heading"><span>01</span><div><small>REGIÓN</small><strong>Definir área</strong></div></div>
          <div className="search-box">
            <Search size={16} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && void runSearch()}
              placeholder="Buscar ciudad o lugar…"
              aria-label="Buscar ubicación"
            />
            <button onClick={() => void runSearch()} disabled={searching}>
              {searching ? <LoaderCircle className="spin" size={15} /> : "Ir"}
            </button>
            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((result) => (
                  <button key={`${result.latitude}-${result.longitude}`} onClick={() => selectSearchResult(result)}>
                    <MapPin size={14} /><span>{result.display_name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="coordinate-grid">
            <label>LATITUD<input type="number" step="0.000001" value={latitude} onChange={(event) => setLatitude(Number(event.target.value))} /></label>
            <label>LONGITUD<input type="number" step="0.000001" value={longitude} onChange={(event) => setLongitude(Number(event.target.value))} /></label>
          </div>
          <button className={`outline-action ${selectMode ? "active" : ""}`} onClick={() => setSelectMode((value) => !value)}>
            <MousePointer2 size={16} /> {selectMode ? "Dibuja sobre el mapa" : "Seleccionar rectángulo"}
          </button>
          <label className="field-label">RADIO DE TRABAJO <b>{radius} m</b></label>
          <input className="range" type="range" min="100" max="1000" step="50" value={radius} onChange={(event) => setRadius(Number(event.target.value))} />
          <div className="radius-options">
            {[100, 250, 500, 1000].map((value) => <button key={value} className={radius === value ? "active" : ""} onClick={() => setRadius(value)}>{value >= 1000 ? "1 km" : `${value} m`}</button>)}
          </div>

          <div className="panel-heading section"><span>02</span><div><small>FUENTES</small><strong>Datos geográficos</strong></div></div>
          <div className="source-list">
            {providers.map((provider) => (
              <SourceBadge key={provider.id} provider={provider} selected={selectedProviders.includes(provider.id)} onToggle={() => toggleProvider(provider.id)} />
            ))}
          </div>
          <label className="toggle-row">
            <span><Database size={15} /> Incluir carreteras</span>
            <input type="checkbox" checked={includeRoads} onChange={(event) => setIncludeRoads(event.target.checked)} />
          </label>
          <label className="toggle-row disabled" title="Se implementará en la fase de relieve">
            <span><Sparkles size={15} /> Relieve DEM <small>próximamente</small></span>
            <input type="checkbox" disabled />
          </label>
          <GenerationOptions materialStyle={materialStyle} floorHeight={floorHeight}
            unknownHeight={unknownHeight} disabled={busy} onMaterialStyle={setMaterialStyle}
            onFloorHeight={setFloorHeight} onUnknownHeight={setUnknownHeight} />
          <button className="generate-button" onClick={() => void generate()} disabled={!canGenerate || ACTIVE_STATUSES.has(job?.status ?? "")}>
            {job && ACTIVE_STATUSES.has(job.status) ? <LoaderCircle className="spin" size={18} /> : <Play size={18} fill="currentColor" />}
            {submitting ? "Iniciando…" : job && ACTIVE_STATUSES.has(job.status) ? statusLabels[job.status] : "Generar escenario"}
          </button>
          <p className="fine-print">Área máxima: 1 km de radio · Perfil comercial · Procesamiento local</p>
        </aside>

        <section className="center-stage">
          <div className="view-switcher">
            <button className={activeView === "map" ? "active" : ""} onClick={() => setActiveView("map")}><MapIcon size={15} /> Mapa 2D</button>
            <button className={activeView === "3d" ? "active" : ""} onClick={() => setActiveView("3d")} disabled={!modelUrl}><Box size={15} /> Escena 3D</button>
          </div>
          {activeView === "map" || !modelUrl ? (
            <AreaMap
              latitude={latitude}
              longitude={longitude}
              radius={radius}
              selectMode={selectMode}
              onCenterChange={(lat, lon) => { setLatitude(lat); setLongitude(lon); }}
              onAreaChange={(lat, lon, nextRadius) => { setLatitude(lat); setLongitude(lon); setRadius(nextRadius); setSelectMode(false); }}
            />
          ) : (
            <ViewerErrorBoundary key={modelUrl} onReturn={() => setActiveView("map")}>
            <Suspense fallback={<div className="stage-loading"><LoaderCircle className="spin" size={24} /> Preparando visor 3D…</div>}>
              <SceneViewer modelUrl={modelUrl} />
            </Suspense>
            </ViewerErrorBoundary>
          )}
          <div className="stage-status">
            <span><MapPin size={13} /> UTM {latitude < 0 ? "sur" : "norte"} · Metros</span>
            <span>{Math.round(Math.PI * radius * radius / 10_000) / 100} km²</span>
          </div>
        </section>

        <aside className="right-panel panel-scroll">
          <div className="inspector-title"><div><small>INSPECTOR</small><strong>Calidad y objeto</strong></div><ChevronDown size={16} /></div>
          <section className="metric-hero">
            <div><small>EDIFICIOS ÚNICOS</small><strong>{quality?.unique_buildings ?? "—"}</strong><span>{quality ? `${quality.raw_buildings} observaciones` : "Genere una escena"}</span></div>
            <Building2 size={34} />
          </section>
          <div className="metric-grid">
            <div><small>VÍAS</small><strong>{quality?.roads ?? "—"}</strong></div>
            <div><small>DUPLICADOS</small><strong>{quality?.duplicates_merged ?? "—"}</strong></div>
            <div><small>CONFLICTOS</small><strong>{quality?.conflicts ?? "—"}</strong></div>
            <div><small>ALTURA EXPL.</small><strong>{quality ? `${quality.height.explicit_percent}%` : "—"}</strong></div>
          </div>
          <section className="inspector-section">
            <div className="section-title"><span>Fiabilidad de alturas</span><small>reproducible</small></div>
            {heightSummary.length ? heightSummary.map(([label, value, kind]) => (
              <div className="legend-row" key={kind}><i className={`dot ${kind}`} /><span>{label}</span><b>{value}</b></div>
            )) : <p className="empty-copy">La distribución aparecerá al terminar la generación.</p>}
          </section>
          <section className="inspector-section">
            <div className="section-title"><span>Estilo visual</span></div>
            <select aria-label="Estilo visual" value={viewerStyle} onChange={(event) => setViewerStyle(event.target.value as ViewerStyle)}>
              <option value="cartographic">Cartográfico</option>
              <option value="architectural">Arquitectónico</option>
              <option value="night">Nocturno</option>
              <option value="gis">Análisis GIS</option>
            </select>
          </section>
          {quality && <section className="inspector-section quality-notes">
            <div className="section-title"><span>Fuentes y límites del modelo</span></div>
            <p>Escala métrica · Terreno plano · Cubiertas planas</p>
            {Object.entries(quality.buildings_by_source_before_fusion).map(([source, count]) => (
              <div className="legend-row" key={source}><span /><span>{source === "osm" ? "OpenStreetMap" : "Overture"}</span><b>{count}</b></div>
            ))}
            <p>Recuentos antes de fusionar duplicados.</p>
            {job?.request.material_style === "procedural" && <p>Fachadas decorativas incluidas en el GLB. Use Arquitectónico para verlas.</p>}
            <details><summary>Advertencias ({quality.warnings.length})</summary>
              {quality.warnings.map((warning, index) => <p key={index}>{warning}</p>)}
            </details>
          </section>}
          <section className="inspector-section selected-object">
            <div className="section-title"><span>Objeto seleccionado</span>{selectedFeature && <MousePointer2 size={14} />}</div>
            {selectedFeature ? (
              <dl>
                <div><dt>ID</dt><dd>{selectedFeature.feature_id}</dd></div>
                <div><dt>Fuente</dt><dd>{selectedFeature.geometry_source ?? selectedFeature.source}</dd></div>
                {selectedFeature.height_m != null && <div><dt>Altura</dt><dd>{selectedFeature.height_m.toFixed(1)} m · {selectedFeature.height_type}</dd></div>}
                {selectedFeature.road_class && <div><dt>Clase</dt><dd>{selectedFeature.road_class}</dd></div>}
              </dl>
            ) : <p className="empty-copy">Seleccione una malla en la vista 3D para inspeccionar su procedencia.</p>}
          </section>
          <section className="inspector-section downloads">
            <div className="section-title"><span>Exportar</span></div>
            <a className={!job || job.status !== "completed" ? "disabled" : ""} href={job ? api.artifactUrl(job.id, "model") : undefined}><Download size={15} /> Modelo GLB <small>mallas reales</small></a>
            <a className={!job || job.status !== "completed" ? "disabled" : ""} href={job ? api.artifactUrl(job.id, "metadata") : undefined}><Download size={15} /> Metadatos JSON</a>
            <a className={!job || job.status !== "completed" ? "disabled" : ""} href={job ? api.artifactUrl(job.id, "attributions") : undefined}><Download size={15} /> Atribuciones</a>
          </section>
        </aside>
      </section>

      <footer className="job-console">
        <div className="job-summary">
          <span className={`status-light ${job?.status ?? "idle"}`} />
          <div><small>TRABAJO</small><strong>{job ? statusLabels[job.status] : "Listo para generar"}</strong></div>
          {job && <code>{job.id.slice(0, 8)}</code>}
        </div>
        <div className="progress-track"><span style={{ width: `${job?.progress ?? 0}%` }} /></div>
        <div className="latest-event" role={visibleError ? "alert" : "status"} title={visibleError ?? job?.events.at(-1)?.message}>
          {visibleError ? <><CircleAlert size={15} /> {visibleError}</> : job?.events.at(-1)?.message ?? "Seleccione una región y las fuentes de datos."}
        </div>
        {job && ACTIVE_STATUSES.has(job.status) && <button disabled={job.cancel_requested} onClick={() => void cancelGeneration()}><X size={14} /> {job.cancel_requested ? "Cancelando…" : "Cancelar"}</button>}
      </footer>
    </main>
  );
}

