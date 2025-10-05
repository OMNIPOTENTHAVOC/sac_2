import os
import requests
from typing import Optional, List, Dict

NASA_API_KEY = os.getenv("NASA_API_KEY", "C1dKltExOkfU7PNIDRAvc3rBvQWaFoyEKZNZhb3C")

NEOWS_BROWSE_URL = "https://api.nasa.gov/neo/rest/v1/neo/browse"
NEOWS_LOOKUP_URL = "https://api.nasa.gov/neo/rest/v1/neo/{}"
SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"

def neows_search_by_name(name: str, max_pages: int = 20) -> Optional[dict]:
    """Search NeoWs browse pages for a near-Earth object whose name contains `name`."""
    name = name.strip().lower()
    page = 0
    per_page = 20
    while page < max_pages:
        params = {"page": page, "size": per_page, "api_key": NASA_API_KEY}
        resp = requests.get(NEOWS_BROWSE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        neos = data.get("near_earth_objects", [])
        for neo in neos:
            if name in (neo.get("name", "").lower()):
                return neo
        links = data.get("links", {})
        if not links or not links.get("next"):
            break
        page += 1
    return None

def neows_get_by_id(spkid: str) -> dict:
    """Lookup NeoWs object by id (SPK-ID)."""
    url = NEOWS_LOOKUP_URL.format(spkid)
    resp = requests.get(url, params={"api_key": NASA_API_KEY}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def sentry_summary() -> dict:
    """Query the JPL Sentry API summary (mode = S)."""
    resp = requests.get(SENTRY_URL, params={"mode": "S"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


# --- NEW: functions needed by app.py ---

def fetch_neos() -> List[Dict]:
    """
    Fetch a list of NEOs from NeoWs.
    Returns a simplified dict list with: name, id, estimated diameter (m), velocity (km/s), hazardous flag.
    """
    neos = []
    page = 0
    per_page = 20
    max_pages = 5  # limit for demo
    while page < max_pages:
        params = {"page": page, "size": per_page, "api_key": NASA_API_KEY}
        resp = requests.get(NEOWS_BROWSE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for neo in data.get("near_earth_objects", []):
            est_diameter = neo.get("estimated_diameter", {}).get("meters", {})
            avg_diam = (est_diameter.get("estimated_diameter_min", 0) +
                        est_diameter.get("estimated_diameter_max", 0)) / 2

            # --- Safe access for close_approach_data ---
            cad = neo.get("close_approach_data", [])
            if cad and len(cad) > 0:
                velocity_km_s = float(cad[0].get("relative_velocity", {}).get("kilometers_per_second", 0))
            else:
                velocity_km_s = 0.0  # fallback if no approach data

            neos.append({
                "name": neo.get("name"),
                "id": neo.get("id"),
                "diameter_m": avg_diam,
                "velocity_km_s": velocity_km_s,
                "hazardous": neo.get("is_potentially_hazardous_asteroid", False)
            })
        page += 1
    return neos

def extract_dangerous_objects(neos: List[Dict]) -> List[Dict]:
    """
    Filter NEOs for potentially hazardous asteroids.
    """
    return [neo for neo in neos if neo.get("hazardous", False)]


if __name__ == "__main__":
    # Quick demo
    neos = fetch_neos()
    print(f"Fetched {len(neos)} NEOs")
    hazards = extract_dangerous_objects(neos)
    print(f"Potentially hazardous: {len(hazards)}")

