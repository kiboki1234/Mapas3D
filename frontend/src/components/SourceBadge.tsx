import { CheckCircle2, CircleOff } from "lucide-react";
import type { ProviderInfo } from "../types";

export function SourceBadge({
  provider,
  selected,
  onToggle,
}: {
  provider: ProviderInfo;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      className={`source-card ${selected ? "selected" : ""}`}
      onClick={onToggle}
      disabled={!provider.available}
      title={provider.detail ?? provider.limitations.join(" ")}
    >
      <span className="source-icon">
        {provider.available ? <CheckCircle2 size={17} /> : <CircleOff size={17} />}
      </span>
      <span>
        <strong>{provider.id === "overture" ? "Overture" : "OpenStreetMap"}</strong>
        <small>{provider.available ? provider.license : "No disponible"}</small>
      </span>
    </button>
  );
}

