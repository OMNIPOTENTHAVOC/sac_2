# orbital.py
"""
orbital.py — orbital propagation & simple deflection modeling for ImpactorViz

This module provides two main capabilities:
1. Predict approximate Earth impact coordinates given entry vector & orbital elements.
2. Simulate how a small velocity change (Δv) applied before impact shifts the point of impact.

This is a simplified physical model suitable for educational and planning visualization.
For mission-grade work, replace with NASA's GMAT, Orekit, or poliastro.
"""

import math
import numpy as np
from pyproj import Geod

EARTH_RADIUS_KM = 6371.0
geod = Geod(ellps="WGS84")

def predict_impact_point(lat_entry: float, lon_entry: float, velocity_km_s: float,
                         flight_path_angle_deg: float, entry_altitude_km: float = 120.0) -> tuple:
    """
    Estimate approximate surface impact point given entry interface location and velocity vector.

    Args:
        lat_entry: Latitude of entry interface (deg)
        lon_entry: Longitude of entry interface (deg)
        velocity_km_s: Velocity at entry (km/s)
        flight_path_angle_deg: Angle of entry relative to local horizontal (deg)
        entry_altitude_km: Altitude of entry interface (km), default ~120 km

    Returns:
        (lat_impact, lon_impact): Estimated ground impact lat/lon
    """
    # Time from entry interface to ground impact (simple ballistic estimate)
    vertical_velocity = velocity_km_s * math.sin(math.radians(flight_path_angle_deg))
    if vertical_velocity <= 0:
        raise ValueError("Flight path angle must indicate downward trajectory (> 0).")

    time_to_impact = entry_altitude_km / vertical_velocity  # seconds

    horizontal_velocity = velocity_km_s * math.cos(math.radians(flight_path_angle_deg))
    downrange_km = horizontal_velocity * time_to_impact  # simplistic

    # Assume ground track follows initial azimuth (eastward = 90°, northward = 0°)
    azimuth = 180.0  # default due south if unknown (placeholder, could be input)
    lon_impact, lat_impact, _ = geod.fwd(lon_entry, lat_entry, azimuth, downrange_km * 1000)

    return lat_impact, lon_impact


def simulate_deflection_effect(lat_impact: float, lon_impact: float,
                               delta_v_m_s: float, lead_time_days: float,
                               original_velocity_km_s: float) -> tuple:
    """
    Estimate how a small velocity change (Δv) applied before impact shifts the ground point.

    Args:
        lat_impact: Original predicted impact latitude (deg)
        lon_impact: Original predicted impact longitude (deg)
        delta_v_m_s: Magnitude of velocity change (m/s)
        lead_time_days: Time before impact when deflection is applied (days)
        original_velocity_km_s: Original orbital velocity (~20 km/s typical)

    Returns:
        (lat_shifted, lon_shifted): New impact coordinates after Δv
    """
    seconds = lead_time_days * 86400.0
    displacement_km = (delta_v_m_s * seconds) / 1000.0

    # Scale by original/orbital velocity — a Δv of 1 m/s at 20 km/s changes impact point slightly
    scale_factor = delta_v_m_s / (original_velocity_km_s * 1000.0)
    downrange_shift_km = displacement_km * scale_factor * 1000  # adjust magnitude

    # Shift impact point along track (default: south)
    azimuth = 180.0
    lon_shifted, lat_shifted, _ = geod.fwd(lon_impact, lat_impact, azimuth, -downrange_shift_km)

    return lat_shifted, lon_shifted


if __name__ == "__main__":
    # Demo example — asteroid entering over 10°N, 80°E, 20 km/s, 30° angle
    lat_entry, lon_entry = 10.0, 80.0
    velocity_km_s = 20.0
    flight_path_angle = 30.0

    lat_impact, lon_impact = predict_impact_point(
        lat_entry, lon_entry, velocity_km_s, flight_path_angle
    )
    print("Predicted impact point:", lat_impact, lon_impact)

    # Deflection scenario: 5 m/s applied 60 days before impact
    lat_shift, lon_shift = simulate_deflection_effect(
        lat_impact, lon_impact, delta_v_m_s=5.0, lead_time_days=60, original_velocity_km_s=velocity_km_s
    )
    print("Shifted impact point:", lat_shift, lon_shift)

