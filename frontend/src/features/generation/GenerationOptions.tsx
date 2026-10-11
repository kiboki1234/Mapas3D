interface Props {
  materialStyle: "plain" | "procedural";
  floorHeight: number;
  unknownHeight: number;
  disabled: boolean;
  onMaterialStyle: (value: "plain" | "procedural") => void;
  onFloorHeight: (value: number) => void;
  onUnknownHeight: (value: number) => void;
}

export function GenerationOptions(props: Props) {
  return (
    <fieldset className="generation-options" disabled={props.disabled}>
      <legend>Modelo 3D</legend>
      <label htmlFor="model-materials">Acabado del modelo</label>
      <select id="model-materials" value={props.materialStyle}
        onChange={(event) => props.onMaterialStyle(event.target.value as Props["materialStyle"])}>
        <option value="plain">Colores de calidad</option>
        <option value="procedural">Fachadas y asfalto</option>
      </select>
      <p>Las texturas son ilustrativas y se incluyen en el GLB. No representan fachadas reales.</p>
      <label htmlFor="floor-height">Altura por piso: {props.floorHeight.toFixed(1)} m</label>
      <input id="floor-height" type="range" min="2" max="6" step="0.1"
        value={props.floorHeight} onChange={(event) => props.onFloorHeight(Number(event.target.value))} />
      <label htmlFor="unknown-height">Altura sin datos: {props.unknownHeight} m</label>
      <input id="unknown-height" type="range" min="2" max="30" step="1"
        value={props.unknownHeight} onChange={(event) => props.onUnknownHeight(Number(event.target.value))} />
      <p>Se conservan las alturas explícitas. Estos valores solo completan datos faltantes.</p>
    </fieldset>
  );
}
