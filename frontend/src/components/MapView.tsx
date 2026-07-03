import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import type { Corridor } from "../types/generated";
import type { GraphNode, GraphResponse, RiskScore, RouteComparisonResult } from "../api/client";
import {
  compareRoute,
  fetchGraph,
  fetchRiskScoresLatest,
} from "../api/client";
import {
  ALTERNATE_ROUTES,
  CORRIDOR_MAP_CENTERS,
  LatLngTuple,
  MAP_CENTER,
  MAP_ZOOM,
  MARITIME_NODE_COORDS,
  PRIMARY_ROUTES,
} from "../geo/routes";
import { scoreByCorridor, scoreToHex } from "../utils/riskColors";
import "leaflet/dist/leaflet.css";

const CORRIDORS: Corridor[] = ["HORMUZ", "BAB_EL_MANDEB", "MALACCA", "OTHER"];

function nodeRadius(node: GraphNode): number {
  if (node.node_type === "CORRIDOR") return 14;
  if (node.node_type === "PORT" || node.node_type === "REFINERY") return 8;
  return 6;
}

interface MapViewProps {
  selectedCorridor: Corridor;
  onCorridorChange: (c: Corridor) => void;
  showDisruption: boolean;
  replayScore?: number | null;
}

/** Component to smoothly pan the map view when selected corridor changes */
function MapRecenter({ center }: { center: LatLngTuple }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 4, { duration: 1.2 });
  }, [center, map]);
  return null;
}

export default function MapView({
  selectedCorridor,
  onCorridorChange,
  showDisruption,
  replayScore,
}: MapViewProps) {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [scores, setScores] = useState<RiskScore[]>([]);
  const [routeComp, setRouteComp] = useState<RouteComparisonResult | null>(null);
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

  // Fetch dynamic backend route comparison whenever selectedCorridor changes
  useEffect(() => {
    let active = true;
    compareRoute(selectedCorridor)
      .then((res) => {
        if (active) setRouteComp(res);
      })
      .catch(() => {
        // Fall back to static route tuples if API fails
      });
    return () => {
      active = false;
    };
  }, [selectedCorridor]);

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
      return "#38bdf8";
    }
    return "#64748b";
  };

  // Convert node path strings to LatLngTuple arrays
  const pathToCoordinates = (pathNodes: string[]): LatLngTuple[] => {
    const coords: LatLngTuple[] = [];
    for (const nid of pathNodes) {
      if (MARITIME_NODE_COORDS[nid]) {
        coords.push(MARITIME_NODE_COORDS[nid]);
      } else if (graph) {
        const found = graph.nodes.find((n) => n.node_id === nid);
        if (found) coords.push([found.lat, found.lon]);
      }
    }
    return coords;
  };

  const dynamicPrimaryRoute = useMemo(() => {
    if (routeComp?.normal?.path && routeComp.normal.path.length > 0) {
      const parsed = pathToCoordinates(routeComp.normal.path);
      if (parsed.length > 1) return parsed;
    }
    return PRIMARY_ROUTES[selectedCorridor] ?? PRIMARY_ROUTES.HORMUZ;
  }, [routeComp, graph, selectedCorridor]);

  const dynamicAlternateRoute = useMemo(() => {
    if (routeComp?.alternative?.path && routeComp.alternative.path.length > 0) {
      const parsed = pathToCoordinates(routeComp.alternative.path);
      if (parsed.length > 1) return parsed;
    }
    return ALTERNATE_ROUTES[selectedCorridor] ?? ALTERNATE_ROUTES.HORMUZ;
  }, [routeComp, graph, selectedCorridor]);

  const currentScoreVal = corridorScore(selectedCorridor);
  const targetCenter = CORRIDOR_MAP_CENTERS[selectedCorridor] ?? MAP_CENTER;

  const rerouteBadgeText = () => {
    if (selectedCorridor === "BAB_EL_MANDEB") return "CAPE / SUEZ BYPASS ACTIVE";
    if (selectedCorridor === "MALACCA") return "SUNDA / LOMBOK BYPASS ACTIVE";
    if (selectedCorridor === "OTHER") return "GLOBAL TRADE ROUTE ACTIVE";
    return "CAPE REROUTE ACTIVE";
  };

  if (error) {
    return <p className="text-red-300">Map error: {error}</p>;
  }

  return (
    <div className="space-y-4">
      {/* Floating Tactical Top Control Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-glass p-3 px-5 rounded-2xl border border-slate-800/80 shadow-2xl">
        <div className="flex items-center gap-3">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-sky-500" />
          </span>
          <label htmlFor="map-corridor-select" className="text-xs font-extrabold uppercase tracking-widest text-slate-300 font-mono">
            COMMAND MAP FOCUS:
          </label>
          <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
            {CORRIDORS.map((c) => (
              <button
                key={c}
                type="button"
                disabled={replayScore !== undefined}
                onClick={() => onCorridorChange(c)}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all duration-300 ${
                  selectedCorridor === c
                    ? "bg-gradient-to-r from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/20 font-black"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                } ${replayScore !== undefined ? "cursor-not-allowed opacity-60" : ""}`}
              >
                {c.replace(/_/g, " ")}
              </button>
            ))}
          </div>

          {/* Hidden select for test automation compatibility */}
          <select
            id="map-corridor-select"
            disabled={replayScore !== undefined}
            className="sr-only"
            value={selectedCorridor}
            onChange={(e) => onCorridorChange(e.target.value as Corridor)}
          >
            {CORRIDORS.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          {showDisruption && (
            <span className="rounded-lg bg-rose-500/15 text-rose-300 border border-rose-500/30 px-3 py-1 text-[11px] font-extrabold uppercase tracking-wider shadow-md shadow-rose-500/20 animate-pulse">
              ⚠️ DISRUPTION SIMULATION ACTIVE
            </span>
          )}
          <span
            id="cape-overlay-badge"
            className={`rounded-lg px-3 py-1 text-[11px] font-extrabold uppercase tracking-wider border transition-all duration-300 ${
              showDisruption
                ? "bg-amber-500/15 text-amber-300 border-amber-500/30 shadow-md shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 border-slate-800"
            }`}
          >
            {rerouteBadgeText()}
          </span>
        </div>
      </div>

      {/* Main Map Canvas Box with Floating Tactical HUD Overlay */}
      <div
        id="setu-map-container"
        className="h-[600px] w-full overflow-hidden rounded-2xl border border-slate-800/80 shadow-2xl shadow-black/80 bg-[#070b14] relative group"
      >
        {/* Floating Left Overlay Panel (Threat Metrics HUD) */}
        <div className="absolute top-4 left-4 z-[1000] w-72 bg-glass-heavy p-4 rounded-xl border border-slate-800/90 shadow-2xl pointer-events-auto space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 font-mono">Corridor Telemetry</span>
            <span className="text-[10px] font-bold font-mono text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
              {selectedCorridor.replace(/_/g, " ")}
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 font-semibold">Threat Index:</span>
              <span className="font-mono font-bold text-sky-300">{currentScoreVal.toFixed(3)}</span>
            </div>
            <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(8, currentScoreVal * 100))}%` }}
              />
            </div>
            <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pt-1">
              <span>Import Flow Share:</span>
              <span className="text-slate-300 font-bold">
                {selectedCorridor === "HORMUZ" ? "3.0 mbpd (60%)" : selectedCorridor === "BAB_EL_MANDEB" ? "0.8 mbpd (16%)" : "1.2 mbpd (24%)"}
              </span>
            </div>
          </div>
        </div>

        {/* Floating Right Overlay Panel (Reroute Path Stats) */}
        <div className="absolute bottom-6 right-4 z-[1000] w-80 bg-glass-heavy p-4 rounded-xl border border-slate-800/90 shadow-2xl pointer-events-auto space-y-2.5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 font-mono">
              {selectedCorridor.replace(/_/g, " ")} ROUTE TELEMETRY
            </span>
            <span className="text-[10px] font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-mono">
              DYNAMIC DIJKSTRA
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-950/60 p-2 rounded border border-slate-800/60">
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Extra Days</span>
              <span className="font-mono font-bold text-amber-400 text-sm">
                +{routeComp ? routeComp.comparison.extra_days.toFixed(1) : "15.2"} Days
              </span>
            </div>
            <div className="bg-slate-950/60 p-2 rounded border border-slate-800/60">
              <span className="text-[9px] font-bold text-slate-500 block uppercase">Extra Cost</span>
              <span className="font-mono font-bold text-rose-400 text-sm">
                +${routeComp ? (routeComp.comparison.extra_cost_usd / 1000).toFixed(0) : "548"}k / trip
              </span>
            </div>
          </div>
          <div className="text-[10px] font-mono text-slate-400 flex justify-between pt-1 border-t border-slate-900">
            <span>VLCC Daily Fuel Burn:</span>
            <span className="text-slate-200 font-bold">$36,000/day</span>
          </div>
        </div>

        <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} className="h-full w-full">
          <MapRecenter center={targetCenter} />
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

          {/* Dynamic Normal Route Line (Cyan) */}
          <Polyline
            positions={dynamicPrimaryRoute}
            color="#38bdf8"
            weight={showDisruption ? 5 : 3.5}
            opacity={showDisruption ? 0.9 : 0.85}
          />

          {/* Dynamic Alternate Reroute Line (Dashed Amber) */}
          <Polyline
            positions={dynamicAlternateRoute}
            color="#f59e0b"
            weight={showDisruption ? 5 : 3.5}
            dashArray="10 8"
            opacity={showDisruption ? 1 : 0.9}
          />

          {graph?.nodes.map((node) => (
            <CircleMarker
              key={node.node_id}
              center={[node.lat, node.lon]}
              radius={nodeRadius(node)}
              pathOptions={{
                color: colorForNode(node),
                fillColor: colorForNode(node),
                fillOpacity: 0.9,
                weight: node.node_type === "CORRIDOR" ? 4 : 2,
              }}
            >
              <Popup className="custom-dark-popup">
                <div className="p-1 font-sans text-slate-900">
                  <div className="font-extrabold text-sm">{node.name}</div>
                  <div className="text-xs text-slate-600 font-bold uppercase mt-0.5">{node.node_type}</div>
                  {node.node_type === "CORRIDOR" && (
                    <div className="mt-2 text-xs font-mono font-bold bg-slate-100 p-1.5 rounded">
                      Threat Index: {(corridorKey(node.node_id) ? corridorScore(corridorKey(node.node_id)!) : 0).toFixed(3)}
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}