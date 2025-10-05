# exposure.py
"""
Population exposure calculation using WorldPop raster
"""

import math
from typing import Union

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from pyproj import Geod


def load_population_raster(path):
    """Load raster using rasterio"""
    return rasterio.open(path)


geod = Geod(ellps="WGS84")


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def population_within_radius(
    raster: rasterio.io.DatasetReader,
    lat: Union[float, int],
    lon: Union[float, int],
    radius_km: Union[float, int],
) -> float:
    """
    Safe version: sums population within radius_km around lat/lon
    Handles edge-of-raster issues.
    """
    # convert radius to degrees approx
    radius_deg = float(radius_km) / 111.0
    minx = float(lon) - radius_deg
    maxx = float(lon) + radius_deg
    miny = float(lat) - radius_deg
    maxy = float(lat) + radius_deg

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
    win = ((row_min, row_max + 1), (col_min, col_max + 1))
    band = raster.read(1, window=win)  # 2-D array for band 1

    # compute cell coordinates
    # NOTE: Avoid raster.xy on 2-D index arrays because it returns 1-D vectors.
    # Build 2-D lon/lat grids using the window-aware affine transform instead.
    rows2d, cols2d = np.indices(band.shape)
    wt = window_transform(win, raster.transform)
    # Affine mapping from pixel indices (col,row) to georeferenced (x,y)
    xs = wt.c + cols2d * wt.a + rows2d * wt.b
    ys = wt.f + cols2d * wt.d + rows2d * wt.e

    # If raster is geographic (EPSG:4326), xs=lons and ys=lats already.
    # Otherwise, transform to WGS84 for distance computation.
    if raster.crs and raster.crs.is_geographic:
        lons = xs
        lats = ys
    else:
        transformer = Transformer.from_crs(raster.crs, "EPSG:4326", always_xy=True)
        lons, lats = transformer.transform(xs, ys)

    # Vectorized haversine distance in km from (lat, lon) to every pixel center
    phi1 = math.radians(float(lat))
    phi2 = np.radians(lats)
    dphi = np.radians(lats - float(lat))
    dlambda = np.radians(lons - float(lon))
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    dist_km = 2 * 6371.0 * np.arcsin(np.sqrt(a))

    # Sum population where pixel value is valid and within the circle
    valid = (band > 0) & (~np.isnan(band)) & (dist_km <= float(radius_km))
    total_pop = float(np.nansum(band[valid]))
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
