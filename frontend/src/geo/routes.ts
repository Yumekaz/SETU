/**
 * Geographic coordinates and route polylines for SETU corridors.
 */

export type LatLngTuple = [number, number];

export const MARITIME_NODE_COORDS: Record<string, LatLngTuple> = {
  persian_gulf: [26.65, 50.17],
  hormuz: [26.57, 56.25],
  gulf_of_aden: [12.58, 43.33],
  malacca: [1.27, 103.75],
  suez_canal: [30.46, 32.34],
  cape_of_good_hope: [-34.36, 18.50],
  jamnagar: [22.47, 69.67],
  mumbai: [18.95, 72.95],
  kochi: [9.97, 76.27],
  chennai: [13.22, 80.32],
  se_asia: [4.93, 114.95],
  arabian_sea: [15.00, 65.00],
  red_sea_north: [27.50, 34.00],
  mediterranean: [35.00, 25.00],
  atlantic_west_africa: [5.00, -5.00],
  mozambique_channel: [-15.00, 42.00],
};

/** Primary routes per corridor */
export const PRIMARY_ROUTES: Record<string, LatLngTuple[]> = {
  HORMUZ: [
    MARITIME_NODE_COORDS.persian_gulf,
    MARITIME_NODE_COORDS.hormuz,
    MARITIME_NODE_COORDS.arabian_sea,
    MARITIME_NODE_COORDS.jamnagar,
  ],
  BAB_EL_MANDEB: [
    MARITIME_NODE_COORDS.persian_gulf,
    MARITIME_NODE_COORDS.gulf_of_aden,
    MARITIME_NODE_COORDS.red_sea_north,
    MARITIME_NODE_COORDS.suez_canal,
  ],
  MALACCA: [
    MARITIME_NODE_COORDS.se_asia,
    MARITIME_NODE_COORDS.malacca,
    MARITIME_NODE_COORDS.chennai,
    MARITIME_NODE_COORDS.kochi,
  ],
};

/** Alternate reroutes per corridor */
export const ALTERNATE_ROUTES: Record<string, LatLngTuple[]> = {
  HORMUZ: [
    MARITIME_NODE_COORDS.persian_gulf,
    MARITIME_NODE_COORDS.gulf_of_aden,
    MARITIME_NODE_COORDS.mozambique_channel,
    MARITIME_NODE_COORDS.cape_of_good_hope,
    MARITIME_NODE_COORDS.atlantic_west_africa,
    MARITIME_NODE_COORDS.jamnagar,
  ],
  BAB_EL_MANDEB: [
    MARITIME_NODE_COORDS.persian_gulf,
    MARITIME_NODE_COORDS.gulf_of_aden,
    MARITIME_NODE_COORDS.mozambique_channel,
    MARITIME_NODE_COORDS.cape_of_good_hope,
    MARITIME_NODE_COORDS.atlantic_west_africa,
    MARITIME_NODE_COORDS.suez_canal,
  ],
  MALACCA: [
    MARITIME_NODE_COORDS.se_asia,
    [ -8.0, 115.0 ], // Lombok Strait bypass
    [ -12.0, 95.0 ], // South Indian Ocean
    MARITIME_NODE_COORDS.chennai,
  ],
};

/** Backward compatibility exports */
export const HORMUZ_PRIMARY_ROUTE = PRIMARY_ROUTES.HORMUZ;
export const CAPE_REROUTE = ALTERNATE_ROUTES.HORMUZ;

export const CORRIDOR_MAP_CENTERS: Record<string, LatLngTuple> = {
  HORMUZ: [22.0, 62.0],
  BAB_EL_MANDEB: [18.0, 48.0],
  MALACCA: [5.0, 95.0],
};

export const MAP_CENTER: LatLngTuple = [15.0, 65.0];
export const MAP_ZOOM = 3;