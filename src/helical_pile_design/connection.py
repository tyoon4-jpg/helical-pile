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

    def sum_ci_squared_m2(self) -> float:
        """Sum(ci^2) for the worst-case bending axis, n bolts evenly spaced.
        For n=4 on a square pattern this reduces to 2*r^2 (doc worked example)."""
        angles = [2 * math.pi * i / self.n_bolts for i in range(self.n_bolts)]
        return sum((self.bolt_circle_radius_m * math.cos(a)) ** 2 for a in angles)


@dataclass
class BoltCheckResult:
    T_bolt_kN: float
    T_capacity_kN: float
    passes: bool


def bolt_tension_kN(M_kNm: float, bolts: BoltGroup, P_uplift_kN: float = 0.0) -> float:
    """T_bolt = M*c_max/Sum(ci^2) + P_uplift/n. Doc eq. 8.2."""
    c_max = bolts.bolt_circle_radius_m
    sum_ci2 = bolts.sum_ci_squared_m2()
    return M_kNm * c_max / sum_ci2 + P_uplift_kN / bolts.n_bolts


def bolt_check(M_kNm: float, bolts: BoltGroup, P_uplift_kN: float = 0.0,
                phi_t: float = PHI_T_BOLT) -> BoltCheckResult:
    T_bolt = bolt_tension_kN(M_kNm, bolts, P_uplift_kN)
    T_cap = phi_t * 0.75 * bolts.Fu_kpa * bolts.Ab_m2
    return BoltCheckResult(T_bolt_kN=T_bolt, T_capacity_kN=T_cap, passes=T_bolt <= T_cap)


def bolt_bending_stress_kpa(V_kN: float, n_bolts: int, standoff_m: float, Ab_m2: float,
                             bolt_diam_m: float) -> float:
    """Additional bolt bending stress from leveling-nut standoff, if
    standoff exceeds one bolt diameter. Doc Section 8.2:
        M_b = (V/n) * standoff / 2
    Returned as an equivalent stress addend (M_b / section modulus of the
    bolt is left to the caller since it depends on thread root area).
    """
    if standoff_m <= bolt_diam_m:
        return 0.0
    shear_per_bolt = V_kN / n_bolts
    return shear_per_bolt * standoff_m / 2.0  # kN*m; combine with bolt Z as needed


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
