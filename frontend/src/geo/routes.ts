/**
 * Demo geographic overlays — ASSUMPTION: graph edges lack lat/lon polylines.
 * Waypoints approximate Hormuz direct vs Cape of Good Hope reroute for demo map.
 */

export type LatLngTuple = [number, number];

/** Gulf production → Hormuz → Mumbai (primary corridor path). */
export const HORMUZ_PRIMARY_ROUTE: LatLngTuple[] = [
  [25.2, 55.3],
  [26.5, 56.5],
  [20.0, 62.0],
  [15.0, 68.0],
  [18.9, 72.8],
];

/** Cape of Good Hope alternate when Hormuz is disrupted. */
export const CAPE_REROUTE: LatLngTuple[] = [
  [25.2, 55.3],
  [20.0, 58.0],
  [10.0, 50.0],
  [-5.0, 40.0],
  [-20.0, 25.0],
  [-35.0, 18.0],
  [-25.0, 35.0],
  [0.0, 55.0],
  [10.0, 75.0],
  [18.9, 72.8],
];

export const MAP_CENTER: LatLngTuple = [15.0, 65.0];
export const MAP_ZOOM = 3;