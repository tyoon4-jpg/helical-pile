"""
Step 1 -- Load determination.

Purpose
-------
Establish factored and service base reactions (V, M, P) at the groundline
from pole/luminaire geometry and wind climate, per AASHTO LTS-6 (or ASCE
7-22 if the project governs that way -- see `wind_pressure_asce7`).

Reference: Design Procedure doc, Section 1.
"""
from __future__ import annotations

from dataclasses import dataclass


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

@dataclass
class PoleGeometry:
    """A1-A3. All lengths in meters, weight in kN."""
    height_m: float                  # h
    base_diam_m: float                # b_base
    top_diam_m: float                 # b_top
    projected_area_m2: float          # A_pole
    weight_kN: float                  # pole + arm weight
    Cd: float = 0.475                 # round tapered, 0.45-0.50 (LTS-6 table) [verify]


@dataclass
class LuminaireLoad:
    """A4-A5. EPA already includes Cd."""
    epa_m2: float
    weight_kN: float
    arm_eccentricity_m: float = 0.0   # e_arm, for torsion T_z = F_lum * e_arm


@dataclass
class WindEnvironment:
    """A6-A7 plus the exposure coefficients used at each relevant height.

    Kz values must come from the AASHTO LTS-6 exposure table (or ASCE 7-22
    Table 26.10-1) for the project's exposure category and the two heights
    of interest: pole-top / component height, and the area centroid z_bar.
    """
    V_ms: float            # basic 3-s gust wind speed, strength case
    Kz_top: float          # Kz at luminaire height h
    Kz_centroid: float     # Kz at pole area centroid z_bar
    Kd: float = 0.95       # directionality, round poles [verify code section]
    G: float = 1.14        # gust effect factor (AASHTO LTS-6)
    service_pressure_ratio: float = 0.44   # W_service / W_strength, ~10-yr MRI [verify]


@dataclass
class Reactions:
    """Groundline reactions. V/P in kN, M in kN*m, e in m."""
    V_kN: float
    M_kNm: float
    P_kN: float
    e_m: float             # eccentricity = M / V
    Tz_kNm: float = 0.0    # torsion, if a mast-arm eccentricity is given


# --------------------------------------------------------------------------
# Step 1.1 -- Design wind pressure (AASHTO LTS-6)
# --------------------------------------------------------------------------

def wind_pressure_kpa(Kz: float, Kd: float, G: float, V_ms: float) -> float:
    """Pz = 0.613 * Kz * Kd * G * V^2  [Pa, V in m/s]  -> returns kPa.

    Doc eq. 1.1. If the project instead governs by ASCE 7-22, use
    `wind_pressure_asce7_kpa` and do not mix the two frameworks.
    """
    Pz_pa = 0.613 * Kz * Kd * G * V_ms ** 2
    return Pz_pa / 1000.0


def wind_pressure_asce7_kpa(Kz: float, Kzt: float, Kd: float, Ke: float, V_ms: float) -> float:
    """qz = 0.613 * Kz * Kzt * Kd * Ke * V^2  [Pa] -> kPa. ASCE 7-22 Ch. 26.

    Use the appropriate risk-category wind map and gust factor per ASCE 7-22
    Ch. 26 alongside this; do not combine with the LTS-6 formulation above.
    """
    qz_pa = 0.613 * Kz * Kzt * Kd * Ke * V_ms ** 2
    return qz_pa / 1000.0


# --------------------------------------------------------------------------
# Step 1.2 -- Wind forces on components
# --------------------------------------------------------------------------

def centroid_height_m(h: float, b_base: float, b_top: float) -> float:
    """z_bar for a linearly tapered pole (trapezoid area centroid). Doc eq. 1.2."""
    return (h / 3.0) * (b_base + 2.0 * b_top) / (b_base + b_top)


def pole_force_kN(Pz_centroid_kpa: float, Cd: float, A_pole_m2: float) -> float:
    """F_pole = Pz(z_bar) * Cd,pole * A_pole."""
    return Pz_centroid_kpa * Cd * A_pole_m2


def luminaire_force_kN(Pz_top_kpa: float, epa_m2: float) -> float:
    """F_lum = Pz(h) * EPA. EPA already includes Cd."""
    return Pz_top_kpa * epa_m2


# --------------------------------------------------------------------------
# Step 1.3 / 1.4 -- Base reactions and load combinations
# --------------------------------------------------------------------------

def base_reactions(
    pole: PoleGeometry,
    lum: LuminaireLoad,
    wind: WindEnvironment,
    reveal_m: float = 0.0,
    dead_load_factor: float = 1.0,
    wind_load_factor: float = 1.0,
) -> Reactions:
    """Groundline V, M, P for a given load-factor combination. Doc eq. 1.3/1.4.

    Extreme I (strength):  dead_load_factor=1.0, wind_load_factor=1.0,
                            wind.V_ms = strength-level (long-MRI) wind speed.
    Service I:              same factors, but pass a WindEnvironment whose
                            V_ms (or Kz/pressure) reflects the ~10-yr
                            service wind -- see `service_wind_environment`.
    """
    z_bar = centroid_height_m(pole.height_m, pole.base_diam_m, pole.top_diam_m)

    Pz_centroid = wind_pressure_kpa(wind.Kz_centroid, wind.Kd, wind.G, wind.V_ms)
    Pz_top = wind_pressure_kpa(wind.Kz_top, wind.Kd, wind.G, wind.V_ms)

    F_pole = pole_force_kN(Pz_centroid, pole.Cd, pole.projected_area_m2)
    F_lum = luminaire_force_kN(Pz_top, lum.epa_m2)

    V = wind_load_factor * (F_pole + F_lum)
    M = wind_load_factor * (F_pole * z_bar + F_lum * pole.height_m) + V * reveal_m
    P = dead_load_factor * (pole.weight_kN + lum.weight_kN)
    Tz = wind_load_factor * F_lum * lum.arm_eccentricity_m

    e = M / V if V != 0 else float("inf")
    return Reactions(V_kN=V, M_kNm=M, P_kN=P, e_m=e, Tz_kNm=Tz)


def service_wind_environment(strength_env: WindEnvironment) -> WindEnvironment:
    """Derive an approximate service-level WindEnvironment by scaling V.

    Doc Section 1.4: W_service based on ~10-yr MRI wind, approximated here
    as pressure-equivalent scaling of V (since Pz ~ V^2):
        V_service = V_strength * sqrt(service_pressure_ratio)
    [verify LTS-6 service wind provision for the specific project]
    """
    import math
    scale = math.sqrt(strength_env.service_pressure_ratio)
    return WindEnvironment(
        V_ms=strength_env.V_ms * scale,
        Kz_top=strength_env.Kz_top,
        Kz_centroid=strength_env.Kz_centroid,
        Kd=strength_env.Kd,
        G=strength_env.G,
        service_pressure_ratio=strength_env.service_pressure_ratio,
    )
