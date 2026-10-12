interface Props {
  floorHeight: number;
  disabled: boolean;
  onFloorHeight: (value: number) => void;
  terrainSource: "auto" | "copernicus" | "terrarium" | "local";
  onTerrainSource: (value: Props["terrainSource"]) => void;
  includeTerrain: boolean;
  landcover: boolean;
  onLandcover: (value: boolean) => void;
  refresh: boolean;
  onRefresh: (value: boolean) => void;
}

export function GenerationOptions(props: Props) {
  return (
    <fieldset className="generation-options" disabled={props.disabled}>
      <legend>Modelo 3D</legend>
      <strong>Fidelidad a la fuente</strong>
      <label>Fuente del relieve<select disabled={!props.includeTerrain} value={props.terrainSource}
        onChange={(event) => props.onTerrainSource(event.target.value as Props["terrainSource"])}>
        <option value="auto">Automático · Copernicus → Terrarium</option>
        <option value="copernicus">Copernicus GLO-30 · DSM</option>
        <option value="terrarium">Terrarium · fuentes regionales</option>
        <option value="local">GeoTIFF local seleccionado</option>
      </select></label>
      <p>Copernicus incluye superficies como vegetación y tejados. Para mayor precisión del suelo, use un DTM local.</p>
      <label className="toggle-row"><span>Cobertura del suelo · WorldCover 2021</span>
        <input type="checkbox" disabled={!props.includeTerrain} checked={props.landcover && props.includeTerrain}
          onChange={(event) => props.onLandcover(event.target.checked)} /></label>
      <p>Clasificación de agua, suelo y vegetación; no fotografía ni árboles individuales.</p>
      <p>Geometría y relieve provienen de datos geográficos. Los colores solo identifican calidad y procedencia.</p>
      <label htmlFor="floor-height">Conversión por piso observado: {props.floorHeight.toFixed(1)} m</label>
      <input id="floor-height" type="range" min="2" max="6" step="0.1"
        value={props.floorHeight} onChange={(event) => props.onFloorHeight(Number(event.target.value))} />
      <p>Sin altura ni número de pisos, el edificio se exporta solo como huella: no se inventa volumen.</p>
      <label className="toggle-row"><span>Regenerar sin reutilizar el modelo</span>
        <input type="checkbox" checked={props.refresh} onChange={(event) => props.onRefresh(event.target.checked)} /></label>
      <p>Los datos descargados mantienen su caché; esto vuelve a construir las mallas.</p>
    </fieldset>
  );
}
