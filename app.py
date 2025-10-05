# app.py
"""
Streamlit dashboard for ImpactorViz

- Tabs + columns UI for clarity
- Sidebar source toggle and key status
- Load WorldPop raster once (cached)
- Fetch NEOs with caching to avoid rate limits
- Compute impact effects (crater/blast/thermal)
- Population exposure estimate
- Impact map with click-to-set lat/lon
"""

from dotenv import load_dotenv
load_dotenv()
import os
import time
from typing import Dict, Any, Optional

import streamlit as st
from streamlit_folium import st_folium

# --- Domain imports (existing project modules) ---
from src.neo import fetch_neos, extract_dangerous_objects  # resilient client recommended in neo.py
from src.impact import crater_diameter_km, blast_radius_km, thermal_radiation_radius_km
from src.exposure import load_population_raster, population_within_radius
from src.viz import create_impact_map
from src.config import WORLDPOP_RASTER

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="ImpactorViz", layout="wide")

st.title("ImpactorViz")
st.markdown("Interactive Asteroid Impact Visualization and Exposure Estimator")

# ----------------------------
# Cached helpers
# ----------------------------
@st.cache_resource(show_spinner=False)
def _load_raster_cached(path: str):
    """Load WorldPop raster once (resource cache)."""
    return load_population_raster(path)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch_neos() -> list:
    """Fetch NEOs with a short TTL (5 min) to reduce API pressure."""
    return fetch_neos()

# ----------------------------
# Session state defaults
# ----------------------------
if "impact_lat" not in st.session_state:
    st.session_state.impact_lat = 10.0
if "impact_lon" not in st.session_state:
    st.session_state.impact_lon = 80.0
if "selected_asteroid" not in st.session_state:
    st.session_state.selected_asteroid = None
if "last_fetch_ts" not in st.session_state:
    st.session_state.last_fetch_ts = None

# ----------------------------
# Sidebar controls
# ----------------------------
with st.sidebar:
    st.header("Source")
    option = st.selectbox("Asteroid input", ["Fetch NEOs", "Manual Entry"])

    # API key status and cache hint
    has_key = bool(os.getenv("NASA_API_KEY"))
    if has_key:
        st.success("NASA_API_KEY detected")
    else:
        st.warning("Using DEMO_KEY (heavily rate-limited)")

    st.caption("NEO cache TTL: 300s; raster cached for session.")

# ----------------------------
# Load WorldPop raster once
# ----------------------------
try:
    raster = _load_raster_cached(WORLDPOP_RASTER)
except Exception as e:
    st.error(f"Failed to load population raster: {e}")
    st.stop()

# ----------------------------
# Tabs and layout
# ----------------------------
tab_inputs, tab_effects, tab_map = st.tabs(["Inputs", "Effects", "Map"])

# ----------------------------
# Asteroid Inputs
# ----------------------------
with tab_inputs:
    st.subheader("Asteroid and Location Inputs")

    c1, c2, c3 = st.columns([1, 1, 1])

    # Asteroid Options
    if option == "Fetch NEOs":
        with st.spinner("Fetching NEOs..."):
            try:
                neo_data = _cached_fetch_neos()
                st.session_state.last_fetch_ts = time.strftime("%H:%M:%S")
            except Exception as e:
                st.error(f"NASA API error: {e}\nTip: set NASA_API_KEY to increase limits.")
                neo_data = []

        threats = extract_dangerous_objects(neo_data)
        names = [t["name"] for t in threats] if threats else []
        selected_name = c1.selectbox("Asteroid", names or ["None"])
        asteroid = next((t for t in threats if t["name"] == selected_name), None)

        # Fall back to safe defaults if API returns missing fields
        default_diam = float(asteroid["diameter_m"]) if asteroid and asteroid.get("diameter_m") else 50.0
        default_vel = float(asteroid["velocity_km_s"]) if asteroid and asteroid.get("velocity_km_s") else 20.0

        diameter_m = c2.number_input("Diameter (m)", value=default_diam, min_value=1.0, step=1.0)
        velocity_kms = c3.number_input("Velocity (km/s)", value=default_vel, min_value=0.1, step=0.1)

        st.session_state.selected_asteroid = asteroid["name"] if asteroid else None
        if st.session_state.last_fetch_ts:
            st.caption(f"NEO list cached at ~{st.session_state.last_fetch_ts}")
    else:
        c1.info("Manual asteroid parameters")
        diameter_m = c2.number_input("Diameter (m)", value=50.0, min_value=1.0, step=1.0)
        velocity_kms = c3.number_input("Velocity (km/s)", value=20.0, min_value=0.1, step=0.1)

    # Location pickers (shared for both modes)
    c4, c5 = st.columns([1, 1])
    lat = c4.number_input(
        "Impact Latitude",
        value=float(st.session_state.impact_lat),
        min_value=-90.0,
        max_value=90.0,
        step=0.1,
        format="%.4f",
    )
    lon = c5.number_input(
        "Impact Longitude",
        value=float(st.session_state.impact_lon),
        min_value=-180.0,
        max_value=180.0,
        step=0.1,
        format="%.4f",
    )

    # Validate primary inputs early
    errors = []
    if diameter_m <= 0:
        errors.append("Diameter must be > 0 m.")
    if not (0.1 <= velocity_kms <= 80):
        errors.append("Velocity should be in km/s within 0.1–80.")
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        errors.append("Latitude/Longitude are out of bounds.")
    if errors:
        st.error(" | ".join(errors))
        st.stop()

    # Persist chosen lat/lon
    st.session_state.impact_lat = float(lat)
    st.session_state.impact_lon = float(lon)

# ----------------------------
# Compute impact effects
# ----------------------------
try:
    # Compute impact effects (keep units consistent with src.impact)
    crater_km = crater_diameter_km(diameter_m, velocity_kms)
    blast_km = blast_radius_km(crater_km)
    thermal_km = thermal_radiation_radius_km(crater_km)
except Exception as e:
    st.error(f"Impact calculation failed: {e}")
    st.stop()

# ----------------------------
# Impact Effects
# ----------------------------
with tab_effects:
    st.subheader("Impact Effects")

    m1, m2, m3 = st.columns(3)
    m1.metric("Crater diameter (km)", f"{crater_km:.2f}")
    m2.metric("Blast radius 1 psi (km)", f"{blast_km:.2f}")
    m3.metric("Thermal radius (km)", f"{thermal_km:.2f}")

    # Compute population exposure
    st.subheader("Population Exposure Estimate")
    try:
        exposed = population_within_radius(
            raster,
            float(st.session_state.impact_lat),
            float(st.session_state.impact_lon),
            float(blast_km),
        )
        st.write(f"Population within blast radius: {exposed:,}")
    except Exception as e:
        st.error(f"Exposure calculation failed: {e}")

# ----------------------------
# Impact Map
# ----------------------------
with tab_map:
    st.subheader("Impact Map")
    st.caption("Click on the map to set a new impact point; inputs sync via session state.")

    try:
        m = create_impact_map(
            float(st.session_state.impact_lat),
            float(st.session_state.impact_lon),
            float(blast_km),
            float(thermal_km),
        )
        # Render and capture click events; state may be None on first run
        state = st_folium(m, width=950, height=600) or {}
        clicked = state.get("last_clicked") or {}
        if "lat" in clicked and "lng" in clicked:
            new_lat = float(clicked["lat"])
            new_lon = float(clicked["lng"])
            # Update session if changed
            if (abs(new_lat - st.session_state.impact_lat) > 1e-6) or (abs(new_lon - st.session_state.impact_lon) > 1e-6):
                st.session_state.impact_lat = new_lat
                st.session_state.impact_lon = new_lon
                st.info(f"Selected point: {new_lat:.4f}, {new_lon:.4f} (inputs updated).")
    except Exception as e:
        st.error(f"Map rendering failed: {e}")

# ----------------------------
# Footer / Debug
# ----------------------------
with st.expander("Debug / Context", expanded=False):
    st.write(
        {
            "selected_asteroid": st.session_state.get("selected_asteroid"),
            "impact_lat": st.session_state.impact_lat,
            "impact_lon": st.session_state.impact_lon,
            "crater_km": crater_km,
            "blast_km": blast_km,
            "thermal_km": thermal_km,
        }
    )
