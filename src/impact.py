# impact.py
"""
Impact physics calculations
Crater diameter, blast radius, thermal radiation
"""

import math

EARTH_RADIUS_KM = 6371.0

def kinetic_energy_joules(mass_kg, velocity_km_s):
    """Kinetic energy of asteroid in Joules"""
    return 0.5 * mass_kg * (velocity_km_s * 1000)**2

def crater_diameter_km(diameter_m, velocity_km_s, density_kg_m3=3000):
    """
    Estimate simple crater diameter (Gault scaling)
    diameter_m: asteroid diameter
    velocity_km_s: impact velocity
    """
    energy = kinetic_energy_joules(4/3 * math.pi * (diameter_m/2)**3 * density_kg_m3, velocity_km_s)
    # Empirical scaling (simplified)
    crater_d = 0.01 * energy**(1/4) / 1000  # km
    return crater_d

def blast_radius_km(crater_km):
    """Approximate 1 psi overpressure radius from crater"""
    return crater_km * 2.0  # rough scale

def thermal_radiation_radius_km(crater_km):
    """Approximate thermal radiation radius from crater"""
    return crater_km * 4.0  # rough scale

if __name__ == "__main__":
    d = 50  # meters
    v = 20  # km/s
    crater = crater_diameter_km(d, v)
    blast = blast_radius_km(crater)
    thermal = thermal_radiation_radius_km(crater)
    print(f"Crater: {crater:.2f} km, Blast: {blast:.2f} km, Thermal: {thermal:.2f} km")

