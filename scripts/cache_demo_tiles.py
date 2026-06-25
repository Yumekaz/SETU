#!/usr/bin/env python3
"""Pre-cache OSM tiles for demo bbox (Indian Ocean / Hormuz region)."""

from __future__ import annotations

import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "public" / "tiles"

# Demo bounding box (lat/lon)
MIN_LAT, MAX_LAT = -10.0, 35.0
MIN_LON, MAX_LON = 40.0, 110.0
ZOOM_LEVELS = (3, 4, 5)


def deg2num(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2.0**zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for z in ZOOM_LEVELS:
        x0, y1 = deg2num(MAX_LAT, MIN_LON, z)
        x1, y0 = deg2num(MIN_LAT, MAX_LON, z)
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                dest = OUT / str(z) / str(x) / f"{y}.png"
                if dest.exists():
                    count += 1
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                try:
                    urllib.request.urlretrieve(url, dest)
                    count += 1
                except OSError as exc:
                    print(f"skip {url}: {exc}")
    print(f"cached_or_existing_tiles={count} dir={OUT}")


if __name__ == "__main__":
    main()