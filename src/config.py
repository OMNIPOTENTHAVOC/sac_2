# config.py

import os

# API key for NASA
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

# Default paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
WORLDPOP_RASTER = os.path.join(DATA_DIR, "worldpop_1km_count.tif")

# Earth constants
EARTH_RADIUS_KM = 6371.0

