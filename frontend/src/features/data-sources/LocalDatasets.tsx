import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import type { LocalDataset, LocalDatasetDescription } from "../../types";

interface Props {
  disabled: boolean;
  buildings: string[];
  terrain: string;
  imagery: string;
  onBuildings: (ids: string[]) => void;
  onTerrain: (id: string) => void;
  onImagery: (id: string) => void;
}

export function LocalDatasets({ disabled, buildings, terrain, imagery, onBuildings, onTerrain, onImagery }: Props) {
  const [datasets, setDatasets] = useState<LocalDataset[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const submitting = useRef(false);
  const [description, setDescription] = useState<LocalDatasetDescription>({
    name: "", kind: "buildings", license: "CC-BY-4.0", attribution: "",
    source_date: "", vertical_datum: "", vertical_unit: "m",
  });

  useEffect(() => {
    let active = true;
    api.localDatasets().then((result) => {
      if (active) { setEnabled(result.enabled); setDatasets(result.datasets); }
    }).catch((reason: Error) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const upload = async () => {
    if (!file || submitting.current) return;
    if (description.kind === "buildings" && buildings.length >= 5) {
      setError("Desmarque un dataset antes de importar otro: máximo cinco seleccionados."); return;
    }
    const maxMb = description.kind === "buildings" ? 10 : 64;
    if (file.size > maxMb * 1024 ** 2) { setError(`Máximo ${maxMb} MB; recorte primero el archivo.`); return; }
    submitting.current = true;
    setUploading(true);
    setError("");
    try {
      const result = await api.importDataset(file, { ...description,
        vertical_datum: description.kind === "dtm" || description.kind === "dsm"
          ? description.vertical_datum : "unknown" });
      setDatasets((current) => [...current, result]);
      if (result.kind === "buildings") onBuildings([...buildings, result.id].slice(0, 5));
      else if (result.kind === "imagery") onImagery(result.id);
      else onTerrain(result.id);
      setFile(null);
      if (input.current) input.current.value = "";
    } catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudo importar"); }
    finally { submitting.current = false; setUploading(false); }
  };

  return <details className="local-datasets">
    <summary>Datos locales de mayor detalle</summary>
    <p>Use archivos con permiso de reutilización. Su procedencia es declarada, no certificada por City3D.</p>
    {loading && <p role="status">Consultando archivos…</p>}
    {!loading && !enabled && <p>Importación disponible en el servidor local. En servidores compartidos requiere habilitación y protección de acceso.</p>}
    {error && <p role="alert" className="import-error">{error}</p>}
    <fieldset disabled={disabled || uploading || !enabled}>
      <legend>Fuentes seleccionadas</legend>
      {datasets.filter((item) => item.kind === "buildings").map((item) => <label className="toggle-row" key={item.id}>
        <span>{item.name} · {item.source_date}</span>
        <input type="checkbox" checked={buildings.includes(item.id)}
          disabled={!buildings.includes(item.id) && buildings.length >= 5}
          onChange={(event) => onBuildings(event.target.checked ? [...buildings, item.id] : buildings.filter((id) => id !== item.id))} />
      </label>)}
      <label>Relieve local
        <select value={terrain} onChange={(event) => onTerrain(event.target.value)}>
          <option value="">Sin archivo seleccionado</option>
          {datasets.filter((item) => item.kind === "dtm" || item.kind === "dsm").map((item) =>
            <option key={item.id} value={item.id}>{item.name} · {item.kind.toUpperCase()} · {item.source_date}</option>)}
        </select>
      </label>
      <label>Vista satelital / ortofoto
        <select value={imagery} onChange={(event) => onImagery(event.target.value)}>
          <option value="">Sin imagen seleccionada</option>
          {datasets.filter((item) => item.kind === "imagery").map((item) =>
            <option key={item.id} value={item.id}>{item.name} · {item.source_date}</option>)}
        </select>
      </label>
      <p>Los edificios locales tienen prioridad geométrica al coincidir. Las alturas estimadas nunca sustituyen a las explícitas.</p>
    </fieldset>
    <fieldset disabled={disabled || uploading || !enabled}>
      <legend>Importar archivo</legend>
      <label>Tipo de datos<select value={description.kind} onChange={(event) => {
        setDescription({ ...description, kind: event.target.value as LocalDatasetDescription["kind"] });
        setFile(null); if (input.current) input.current.value = "";
      }}>
        <option value="buildings">Edificios · GeoJSON WGS84</option>
        <option value="dtm">Terreno desnudo · GeoTIFF DTM</option>
        <option value="dsm">Superficie con tejados · GeoTIFF DSM</option>
        <option value="imagery">Ortofoto real · GeoTIFF RGB/RGBA</option>
      </select></label>
      <label>Archivo<input ref={input} type="file" accept={description.kind === "buildings" ? ".geojson,.json" : ".tif,.tiff"}
        onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
      <label>Nombre del conjunto<input maxLength={120} value={description.name}
        onChange={(event) => setDescription({ ...description, name: event.target.value })} /></label>
      <label>Fecha de los datos<input type="date" value={description.source_date}
        onChange={(event) => setDescription({ ...description, source_date: event.target.value })} /></label>
      <label>Licencia del archivo<select value={description.license}
        onChange={(event) => setDescription({ ...description, license: event.target.value as LocalDatasetDescription["license"] })}>
        {(["CC0-1.0", "CC-BY-4.0", "ODbL-1.0", "CDLA-Permissive-2.0"] as const).map((license) => <option key={license}>{license}</option>)}
      </select></label>
      <label>Autor y atribución requerida<input maxLength={500} value={description.attribution}
        onChange={(event) => setDescription({ ...description, attribution: event.target.value })} /></label>
      {(description.kind === "dtm" || description.kind === "dsm") && <>
        <label>Datum vertical documentado<input placeholder="Ej.: EGM2008" maxLength={80} value={description.vertical_datum}
          onChange={(event) => setDescription({ ...description, vertical_datum: event.target.value })} /></label>
        <label>Unidad de elevación<select value={description.vertical_unit}
          onChange={(event) => setDescription({ ...description, vertical_unit: event.target.value as "m" | "ft" })}>
          <option value="m">Metros</option><option value="ft">Pies internacionales</option>
        </select></label>
      </>}
      <p>{description.kind === "buildings"
        ? "Polígonos 2D. Propiedades: height_m (altura sobre el suelo), num_floors, height_estimated y name. No use cotas sobre el nivel del mar como altura. Máximo 10 MB."
        : description.kind === "imagery"
          ? "Imagen RGB o RGBA de 8 bits, con CRS y permiso de reutilización. Debe cubrir toda el área. Máximo 64 MB; recórtela en QGIS."
          : "Una banda con elevaciones, CRS y NoData definidos. No mezcle datums. Máximo 64 MB; recorte en QGIS antes de importar."}</p>
      <button type="button" className="outline-action" onClick={() => void upload()}
        disabled={!file || !description.name.trim() || !description.attribution.trim() || !description.source_date || ((description.kind === "dtm" || description.kind === "dsm") && !description.vertical_datum.trim())}>
        {uploading ? "Validando archivo…" : "Importar y seleccionar"}
      </button>
    </fieldset>
  </details>;
}
