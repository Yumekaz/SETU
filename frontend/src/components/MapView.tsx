import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from "react-leaflet";
import type { Corridor } from "../types/generated";
import {
  fetchGraph,
  fetchRiskScoresLatest,
  type GraphNode,
  type GraphResponse,
  type RiskScore,
} from "../api/client";
import { CAPE_REROUTE, HORMUZ_PRIMARY_ROUTE, MAP_CENTER, MAP_ZOOM } from "../geo/routes";
import { scoreByCorridor, scoreToHex } from "../utils/riskColors";
import "leaflet/dist/leaflet.css";

const CORRIDORS: Corridor[] = ["HORMUZ", "BAB_EL_MANDEB", "MALACCA"];

function nodeRadius(node: GraphNode): number {
  if (node.node_type === "CORRIDOR") return 14;
  if (node.node_type === "PORT" || node.node_type === "REFINERY") return 8;
  return 5;
}

interface MapViewProps {
  selectedCorridor: Corridor;
  onCorridorChange: (c: Corridor) => void;
  showDisruption: boolean;
  replayScore?: number | null;
}

export default function MapView({
  selectedCorridor,
  onCorridorChange,
  showDisruption,
  replayScore,
}: MapViewProps) {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [scores, setScores] = useState<RiskScore[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [useOfflineTiles, setUseOfflineTiles] = useState(false);

  useEffect(() => {
    Promise.all([fetchGraph(), fetchRiskScoresLatest()])
      .then(([g, s]) => {
        setGraph(g);
        setScores(s);
        setError(null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  const scoreMap = useMemo(() => scoreByCorridor(scores), [scores]);

  const corridorScore = (corridor: string): number => {
    if (replayScore != null && corridor === "HORMUZ") return replayScore;
    return scoreMap[corridor] ?? 0;
  };

  const corridorKey = (nodeId: string): string | null => {
    if (!nodeId.startsWith("corridor_")) return null;
    const slug = nodeId.replace("corridor_", "");
    if (slug === "bab_el_mandeb") return "BAB_EL_MANDEB";
    if (slug === "hormuz") return "HORMUZ";
    if (slug === "malacca") return "MALACCA";
    return slug.toUpperCase();
  };

  const colorForNode = (node: GraphNode): string => {
    if (node.node_type === "CORRIDOR") {
      const key = corridorKey(node.node_id);
      return scoreToHex(key ? corridorScore(key) : 0);
    }
    if (selectedCorridor && node.node_id.includes(selectedCorridor.toLowerCase().replace("_", "_"))) {
      return "#0ea5e9";
    }
    return "#64748b";
  };

  if (error) {
    return <p className="text-red-300">Map error: {error}</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-300">Corridor</label>
        <select
          id="map-corridor-select"
          className="rounded bg-slate-800 px-3 py-2 text-sm"
          value={selectedCorridor}
          onChange={(e) => onCorridorChange(e.target.value as Corridor)}
        >
          {CORRIDORS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        {showDisruption && (
          <span className="rounded-full bg-amber-900/50 px-3 py-1 text-xs text-amber-200">
            Disruption emphasis active
          </span>
        )}
        {selectedCorridor === "HORMUZ" && (
          <span
            id="cape-overlay-badge"
            className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400"
          >
            Cape reroute overlay (demo ASSUMPTION)
          </span>
        )}
      </div>
      <div
        id="setu-map-container"
        className="h-[520px] w-full min-w-[720px] overflow-hidden rounded-lg border border-slate-700"
      >
        <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url={
              useOfflineTiles
                ? "/tiles/{z}/{x}/{y}.png"
                : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            }
            eventHandlers={{
              tileerror: () => setUseOfflineTiles(true),
            }}
          />
          {selectedCorridor === "HORMUZ" && (
            <>
              <Polyline
                positions={HORMUZ_PRIMARY_ROUTE}
                color="#22c55e"
                weight={showDisruption ? 4 : 3}
                opacity={showDisruption ? 1 : 0.75}
              />
              <Polyline
                positions={CAPE_REROUTE}
                color="#f59e0b"
                weight={showDisruption ? 4 : 3}
                dashArray="8 6"
                opacity={showDisruption ? 1 : 0.85}
              />
            </>
          )}
          {graph?.nodes.map((node) => (
            <CircleMarker
              key={node.node_id}
              center={[node.lat, node.lon]}
              radius={nodeRadius(node)}
              pathOptions={{
                color: colorForNode(node),
                fillColor: colorForNode(node),
                fillOpacity: 0.85,
                weight: node.node_type === "CORRIDOR" ? 3 : 1,
              }}
            >
              <Popup>
                <strong>{node.name}</strong>
                <br />
                {node.node_type}
                {node.node_type === "CORRIDOR" && (
                  <>
                    <br />
                    Score: {(corridorKey(node.node_id) ? corridorScore(corridorKey(node.node_id)!) : 0).toFixed(3)}
                  </>
                )}
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}