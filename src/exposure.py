# exposure.py
"""
Population exposure calculation using WorldPop raster
"""

import rasterio
import numpy as np
from pyproj import Transformer
from rasterio.windows import Window
from pyproj import Geod
import math


def load_population_raster(path):
    """Load raster using rasterio"""
    return rasterio.open(path)

geod = Geod(ellps="WGS84")

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return 2 * R * math.asin(math.sqrt(a))

def population_within_radius(raster, lat, lon, radius_km):
    """
    Safe version: sums population within radius_km around lat/lon
    Handles edge-of-raster issues.
    """
    # convert radius to degrees approx
    radius_deg = radius_km / 111.0
    minx = lon - radius_deg
    maxx = lon + radius_deg
    miny = lat - radius_deg
    maxy = lat + radius_deg

    try:
        row_min, col_min = raster.index(minx, maxy)
        row_max, col_max = raster.index(maxx, miny)
    except Exception:
        return 0.0  # outside raster bounds

    # clamp to raster bounds
    row_min = max(0, min(row_min, raster.height - 1))
    row_max = max(0, min(row_max, raster.height - 1))
    col_min = max(0, min(col_min, raster.width - 1))
    col_max = max(0, min(col_max, raster.width - 1))

    # make sure rows/cols are valid
    if row_max < row_min:
        row_max = row_min
    if col_max < col_min:
        col_max = col_min

    # read window safely
    window = raster.read(1, window=((row_min, row_max + 1), (col_min, col_max + 1)))
    # compute cell coordinates
    rows, cols = np.indices(window.shape)
    lons, lats = raster.xy(rows + row_min, cols + col_min)
    lons = np.array(lons)
    lats = np.array(lats)

    total_pop = 0.0
    for r, c in np.ndindex(window.shape):
        val = window[r, c]
        if val <= 0 or np.isnan(val):
            continue
        if haversine_km(lat, lon, lats[r, c], lons[r, c]) <= radius_km:
            total_pop += val
    return total_pop

if __name__ == "__main__":
    # Quick test
    import os
    from src.config import WORLDPOP_RASTER

    if not os.path.exists(WORLDPOP_RASTER):
        print("WorldPop raster not found:", WORLDPOP_RASTER)
    else:
        raster = load_population_raster(WORLDPOP_RASTER)
        pop = population_within_radius(raster, lat=10.0, lon=80.0, radius_km=50)
        print(f"Estimated population within 50 km: {pop}")

