#!/usr/bin/env bash
set -e
mkdir -p data

SAMPLE_TIF="data/worldpop_1km_count.tif"

echo "Creating a small synthetic WorldPop-style GeoTIFF at ${SAMPLE_TIF} ..."
python3 - <<'PY'
import numpy as np
import rasterio
from rasterio.transform import from_origin

# create a tiny global-ish grid (360 x 180 -> 1-degree resolution) as demo
width = 360
height = 180
# make synthetic population: high values around (lat ~34N, lon ~-118.25) as demo
arr = np.zeros((height, width), dtype=np.float32)

# Coordinates: we'll use simple lon [-180..179], lat [90..-89]
lons = np.linspace(-179.5, 179.5, width)
lats = np.linspace(89.5, -89.5, height)

# pick a demo center (Los Angeles-ish)
center_lat = 34.0
center_lon = -118.25

# populate values with gaussian falloff
sigma_deg = 2.0  # spread of population cluster
for i, lat in enumerate(lats):
    for j, lon in enumerate(lons):
        dlat = lat - center_lat
        dlon = lon - center_lon
        dist = (dlat**2 + dlon**2)**0.5
        val = 1000.0 * np.exp(-(dist**2) / (2 * sigma_deg**2))
        arr[i, j] = val

transform = from_origin(-180.0, 90.0, 1.0, 1.0)  # cellsize 1 deg
meta = {
    "driver": "GTiff",
    "dtype": "float32",
    "nodata": 0.0,
    "width": width,
    "height": height,
    "count": 1,
    "crs": "EPSG:4326",
    "transform": transform
}
with rasterio.open("data/worldpop_1km_count.tif", "w", **meta) as dst:
    dst.write(arr, 1)

print("Synthetic raster written: data/worldpop_1km_count.tif")
PY

echo "Done. The demo raster is small and will let you run the app immediately."

cat <<'TXT'

-- OPTIONAL: To replace with the real WorldPop mosaic, download manually:
(Example - edit/choose the correct WorldPop URL and file you want.)

# Example (commented out):
# wget -O data/worldpop_1km_count_real.tif "https://example.worldpop-download-link/your-worldpop-file.tif"

After downloading the actual WorldPop GeoTIFF, update the path in the Streamlit sidebar or replace data/worldpop_1km_count.tif.

TXT

