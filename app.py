# app.py
"""
Streamlit dashboard for ImpactorViz
"""

import streamlit as st
from src.neo import fetch_neos, extract_dangerous_objects
from src.impact import crater_diameter_km, blast_radius_km, thermal_radiation_radius_km
from src.exposure import load_population_raster, population_within_radius
from src.viz import create_impact_map
from src.config import WORLDPOP_RASTER

st.set_page_config(page_title="ImpactorViz", layout="wide")

st.title("ImpactorViz")
st.markdown("Interactive Asteroid Impact Visualization and Exposure Estimator")

# Load WorldPop raster once
raster = load_population_raster(WORLDPOP_RASTER)

st.sidebar.header("Asteroid Options")
option = st.sidebar.selectbox("Select input method", ["Fetch NEOs", "Manual Entry"])

if option == "Fetch NEOs":
    st.sidebar.info("Fetching NEOs from NASA API...")
    neo_data = fetch_neos()
    threats = extract_dangerous_objects(neo_data)
    if not threats:
        st.warning("No potentially hazardous objects in the next 7 days")
    else:
        names = [t["name"] for t in threats]
        selected = st.sidebar.selectbox("Select asteroid", names)
        asteroid = next(t for t in threats if t["name"] == selected)
        diameter = asteroid["diameter_m"]
        velocity = asteroid["velocity_km_s"]
        lat, lon = 10.0, 80.0  # placeholder entry lat/lon
else:
    st.sidebar.info("Manual asteroid parameters")
    diameter = st.sidebar.number_input("Diameter (m)", value=50)
    velocity = st.sidebar.number_input("Velocity (km/s)", value=20.0)
    lat = st.sidebar.number_input("Impact Latitude", value=10.0, min_value=-90.0, max_value=90.0)
    lon = st.sidebar.number_input("Impact Longitude", value=80.0, min_value=-180.0, max_value=180.0)

# Compute impact effects
crater = crater_diameter_km(diameter, velocity)
blast = blast_radius_km(crater)
thermal = thermal_radiation_radius_km(crater)

st.subheader("Impact Effects")
st.write(f"Crater diameter: {crater:.2f} km")
st.write(f"Blast radius (~1 psi overpressure): {blast:.2f} km")
st.write(f"Thermal radiation radius: {thermal:.2f} km")

# Compute population exposure
pop_exposed = population_within_radius(raster, lat, lon, blast)
st.subheader("Population Exposure Estimate")
st.write(f"Population within blast radius: {pop_exposed:,}")

# Map visualization
st.subheader("Impact Map")
m = create_impact_map(lat, lon, blast, thermal)
from streamlit_folium import st_folium
st_folium(m, width=700, height=500)

