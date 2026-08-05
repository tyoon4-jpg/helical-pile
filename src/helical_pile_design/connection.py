"""
Step 8 -- Pole-to-pile connection design.

Purpose
-------
Transfer M, V, P, and torsion from the pole base plate into the pile shaft
through an adapter/cap plate, anchor bolts, and a fillet weld.
Reference: Design Procedure doc, Section 8.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

PHI_T_BOLT = 0.75   # AISC 360 J3, bolt tension
PHI_W_WELD = 0.75   # AISC 360 J2, weld


@dataclass
class BoltGroup:
    """Bolt circle geometry. n bolts evenly spaced on a circle of radius r_m."""
    n_bolts: int
    bolt_circle_radius_m: float
    Ab_m2: float           # tensile stress area per bolt
    Fu_kpa: float           # bolt ultimate strength (e.g. F1554 Gr 55/105)
    bolt_diam_m: float      # nominal shank diameter -- used only for the standoff bending check

    def sum_ci_squared_m2(self) -> float:
        """Sum(ci^2) for the worst-case bending axis, n bolts evenly spaced.
        For n=4 on a square pattern this reduces to 2*r^2 (doc worked example)."""
        angles = [2 * math.pi * i / self.n_bolts for i in range(self.n_bolts)]
        return sum((self.bolt_circle_radius_m * math.cos(a)) ** 2 for a in angles)


@dataclass
class BoltCheckResult:
    T_bolt_kN: float
    T_capacity_kN: float
    sigma_tension_kpa: float
    sigma_bending_kpa: float
    sigma_total_kpa: float
    sigma_capacity_kpa: float
    passes: bool


def bolt_tension_kN(M_kNm: float, bolts: BoltGroup, P_uplift_kN: float = 0.0) -> float:
    """T_bolt = M*c_max/Sum(ci^2) + P_uplift/n. Doc eq. 8.2."""
    c_max = bolts.bolt_circle_radius_m
    sum_ci2 = bolts.sum_ci_squared_m2()
    return M_kNm * c_max / sum_ci2 + P_uplift_kN / bolts.n_bolts


def bolt_bending_moment_kNm(V_kN: float, bolts: BoltGroup, standoff_m: float) -> float:
    """Additional bolt bending moment from leveling-nut standoff, if standoff
    exceeds one bolt diameter. Doc Section 8.2: M_b = (V/n) * standoff / 2.

    Returns a MOMENT (kN*m) -- convert to stress with `bolt_section_modulus_m3`
    and combine into `bolt_check`. (Previously named `bolt_bending_stress_kpa`,
    which was misleading: it never returned a stress.)
    """
    if standoff_m <= bolts.bolt_diam_m:
        return 0.0
    shear_per_bolt = V_kN / bolts.n_bolts
    return shear_per_bolt * standoff_m / 2.0


def bolt_section_modulus_m3(bolt_diam_m: float) -> float:
    """Elastic section modulus of a solid circular bolt shank, S = pi*d^3/32.

    Uses the NOMINAL bolt diameter as a stand-in for the (smaller) thread-root
    diameter -- this overestimates S and therefore UNDERESTIMATES bending
    stress. Acceptable for a preliminary screen only; replace with the
    manufacturer's actual thread-root section modulus before final design.
    """
    return math.pi * bolt_diam_m ** 3 / 32.0


def bolt_check(M_kNm: float, bolts: BoltGroup, P_uplift_kN: float = 0.0,
                bending_moment_kNm: float = 0.0, phi_t: float = PHI_T_BOLT) -> BoltCheckResult:
    """Combines axial (tension + uplift) and standoff-bending stress into a
    single combined-stress check, per Doc Section 8.2. With
    `bending_moment_kNm=0.0` (no standoff bending) this reduces exactly to
    the prior tension-only check: T_bolt <= phi_t*0.75*Fu*Ab.
    """
    T_bolt = bolt_tension_kN(M_kNm, bolts, P_uplift_kN)
    sigma_tension = T_bolt / bolts.Ab_m2
    Z_bolt = bolt_section_modulus_m3(bolts.bolt_diam_m)
    sigma_bending = bending_moment_kNm / Z_bolt if Z_bolt > 0 else 0.0
    sigma_total = sigma_tension + sigma_bending
    sigma_capacity = phi_t * 0.75 * bolts.Fu_kpa
    T_cap = sigma_capacity * bolts.Ab_m2  # kept for display -- tension-only capacity in force terms
    return BoltCheckResult(
        T_bolt_kN=T_bolt, T_capacity_kN=T_cap,
        sigma_tension_kpa=sigma_tension, sigma_bending_kpa=sigma_bending,
        sigma_total_kpa=sigma_total, sigma_capacity_kpa=sigma_capacity,
        passes=sigma_total <= sigma_capacity,
    )


@dataclass
class WeldCheckResult:
    demand_kN_per_m: float
    capacity_kN_per_m: float
    passes: bool


def weld_check(
    M_kNm: float, V_kN: float, D_shaft_m: float, fillet_size_m: float,
    FEXX_kpa: float = 490e3, phi_w: float = PHI_W_WELD,
) -> WeldCheckResult:
    """All-around fillet weld, shaft-to-plate, treated as a line. Doc eq. 8.3.
        Sw = pi * r^2,  r = D/2
        w_M = M / Sw ; w_V = V / (pi*D)
        w_r = sqrt(w_M^2 + w_V^2) <= phi_w * 0.6*FEXX*0.707*a
    """
    r = D_shaft_m / 2.0
    Sw = math.pi * r ** 2
    w_M = M_kNm / Sw
    w_V = V_kN / (math.pi * D_shaft_m)
    w_r = math.sqrt(w_M ** 2 + w_V ** 2)
    capacity = phi_w * 0.6 * FEXX_kpa * 0.707 * fillet_size_m
    return WeldCheckResult(demand_kN_per_m=w_r, capacity_kN_per_m=capacity, passes=w_r <= capacity)


def torsion_slip_check(pile_torsional_capacity_kNm: float, Tz_kNm: float, factor: float = 3.0) -> bool:
    """Doc Section 8.4: single-arm poles require pile torsional slip
    resistance >= factor * Tz (default factor = 3)."""
    return pile_torsional_capacity_kNm >= factor * Tz_kNm
