# viz.py
import folium

def create_impact_map(lat, lon, blast_km, thermal_km):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Impact point").add_to(m)
    folium.Circle([lat, lon], radius=blast_km*1000, color="red", fill=True,
                  fill_opacity=0.2, tooltip="~1 psi blast radius").add_to(m)
    folium.Circle([lat, lon], radius=thermal_km*1000, color="orange", fill=True,
                  fill_opacity=0.15, tooltip="Thermal radiation radius").add_to(m)
    return m

