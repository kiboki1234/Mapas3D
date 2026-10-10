import { useEffect, useMemo, useState } from "react";
import L, { type LatLng, type LatLngBounds } from "leaflet";
import { Circle, MapContainer, Rectangle, TileLayer, useMap, useMapEvents } from "react-leaflet";

interface AreaMapProps {
  latitude: number;
  longitude: number;
  radius: number;
  selectMode: boolean;
  onCenterChange: (latitude: number, longitude: number) => void;
  onAreaChange: (latitude: number, longitude: number, radius: number) => void;
}

function MapSync({ latitude, longitude }: Pick<AreaMapProps, "latitude" | "longitude">) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([latitude, longitude], map.getZoom(), { duration: 0.6 });
  }, [latitude, longitude, map]);
  return null;
}

function DrawRectangle({
  enabled,
  onAreaChange,
}: {
  enabled: boolean;
  onAreaChange: AreaMapProps["onAreaChange"];
}) {
  const [start, setStart] = useState<LatLng | null>(null);
  const [bounds, setBounds] = useState<LatLngBounds | null>(null);
  const map = useMapEvents({
    mousedown(event) {
      if (!enabled) return;
      map.dragging.disable();
      setStart(event.latlng);
      setBounds(L.latLngBounds(event.latlng, event.latlng));
    },
    mousemove(event) {
      if (!enabled || !start) return;
      setBounds(L.latLngBounds(start, event.latlng));
    },
    mouseup(event) {
      if (!enabled || !start) return;
      const finalBounds = L.latLngBounds(start, event.latlng);
      const center = finalBounds.getCenter();
      const radius = Math.max(
        50,
        Math.min(1000, Math.round(center.distanceTo(finalBounds.getNorthEast()))),
      );
      setBounds(finalBounds);
      setStart(null);
      map.dragging.enable();
      onAreaChange(center.lat, center.lng, radius);
    },
    click(event) {
      if (!enabled) return;
      event.originalEvent.preventDefault();
    },
  });
  useEffect(() => {
    if (!enabled) {
      setStart(null);
      map.dragging.enable();
    }
  }, [enabled, map]);
  return bounds ? <Rectangle bounds={bounds} pathOptions={{ color: "#54a7ff", weight: 2 }} /> : null;
}

function ClickCenter({
  enabled,
  onCenterChange,
}: {
  enabled: boolean;
  onCenterChange: AreaMapProps["onCenterChange"];
}) {
  useMapEvents({
    click(event) {
      if (!enabled) onCenterChange(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

export function AreaMap(props: AreaMapProps) {
  const center = useMemo<[number, number]>(
    () => [props.latitude, props.longitude],
    [props.latitude, props.longitude],
  );
  return (
    <MapContainer center={center} zoom={16} minZoom={3} className="map-canvas" zoomControl={false}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Circle
        center={center}
        radius={props.radius}
        pathOptions={{ color: "#3b95ff", fillColor: "#3b95ff", fillOpacity: 0.12, weight: 2 }}
      />
      <MapSync latitude={props.latitude} longitude={props.longitude} />
      <DrawRectangle enabled={props.selectMode} onAreaChange={props.onAreaChange} />
      <ClickCenter enabled={props.selectMode} onCenterChange={props.onCenterChange} />
    </MapContainer>
  );
}

