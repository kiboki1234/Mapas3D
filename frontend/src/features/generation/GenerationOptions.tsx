interface Props {
  floorHeight: number;
  disabled: boolean;
  onFloorHeight: (value: number) => void;
}

export function GenerationOptions(props: Props) {
  return (
    <fieldset className="generation-options" disabled={props.disabled}>
      <legend>Modelo 3D</legend>
      <strong>Fidelidad a la fuente</strong>
      <p>Geometría y relieve provienen de datos geográficos. Los colores solo identifican calidad y procedencia.</p>
      <label htmlFor="floor-height">Conversión por piso observado: {props.floorHeight.toFixed(1)} m</label>
      <input id="floor-height" type="range" min="2" max="6" step="0.1"
        value={props.floorHeight} onChange={(event) => props.onFloorHeight(Number(event.target.value))} />
      <p>Sin altura ni número de pisos, el edificio se exporta solo como huella: no se inventa volumen.</p>
    </fieldset>
  );
}
