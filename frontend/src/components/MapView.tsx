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
    if (replayScore != null && corridor === selectedCorridor) return replayScore;
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
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3 bg-glass px-4 py-2.5 rounded-xl border border-slate-900 w-fit">
        <label htmlFor="map-corridor-select" className="text-xs font-bold uppercase tracking-wider text-slate-400">Target Corridor</label>
        <select
          id="map-corridor-select"
          disabled={replayScore !== undefined}
          className={`bg-slate-950/80 border border-slate-900 rounded px-2.5 py-1 text-xs text-sky-400 font-bold outline-none transition-all mr-2 ${
            replayScore !== undefined ? "cursor-not-allowed opacity-60" : "cursor-pointer focus:border-sky-500"
          }`}
          value={selectedCorridor}
          onChange={(e) => onCorridorChange(e.target.value as Corridor)}
        >
          {CORRIDORS.map((c) => (
            <option key={c} value={c}>
              {c.replace(/_/g, " ")}
            </option>
          ))}
        </select>
        {showDisruption && (
          <span className="rounded bg-rose-500/10 px-2.5 py-1 text-[10px] font-bold text-rose-400 border border-rose-500/15 uppercase tracking-wide animate-pulse">
            Active Disruption Overlay
          </span>
        )}
        <span
          id="cape-overlay-badge"
          className="rounded bg-slate-800/40 px-2.5 py-1 text-[10px] font-bold text-slate-500 border border-slate-800/60 uppercase tracking-wide"
        >
          Cape Reroute Active
        </span>
      </div>
      <div
        id="setu-map-container"
        className="h-[550px] w-full overflow-hidden rounded-xl border border-slate-900 shadow-2xl shadow-black/45 bg-[#0e0e11]"
      >
        <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url={
              useOfflineTiles
                ? "/tiles/{z}/{x}/{y}.png"
                : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            }
            eventHandlers={{
              tileerror: () => setUseOfflineTiles(true),
            }}
          />
          {selectedCorridor === "HORMUZ" && (
            <Polyline
              positions={HORMUZ_PRIMARY_ROUTE}
              color="#22c55e"
              weight={showDisruption ? 4 : 3}
              opacity={showDisruption ? 1 : 0.75}
            />
          )}
          <Polyline
            positions={CAPE_REROUTE}
            color="#f59e0b"
            weight={showDisruption ? 4 : 3}
            dashArray="8 6"
            opacity={showDisruption ? 1 : 0.85}
          />
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