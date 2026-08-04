"""
Step 6 -- Shaft structural checks per AISC 360.

Purpose
-------
Verify the steel shaft, AT ITS CORRODED END-OF-LIFE SECTION, for combined
axial + bending, shear, buckling trigger, and installation torsion.
Reference: Design Procedure doc, Section 6.

IMPORTANT: every function here takes `t_c` (corroded wall thickness, Step 7
output). There is deliberately no `t_nominal` parameter -- passing the
nominal wall into a design-life check is exactly the error this module
structure is meant to prevent.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

PHI_B = 0.90   # flexure
PHI_C = 0.90   # compression
PHI_V = 0.90   # shear (round HSS)


@dataclass
class SectionProperties:
    D_m: float
    t_c_m: float
    S_m3: float   # elastic section modulus
    Z_m3: float   # plastic section modulus
    A_m2: float
    compact: bool
    slenderness_ratio: float
    slenderness_limit: float


def section_properties(D_m: float, t_c_m: float, Fy_kpa: float, E_kpa: float = 200e6) -> SectionProperties:
    """Doc eq. 6.1. Corroded pipe section properties + compactness check
    (AISC Table B4.1b): D/t_c <= 0.07*E/Fy for compact round HSS."""
    d_i = D_m - 2 * t_c_m
    S = (math.pi / 32.0) * (D_m ** 4 - d_i ** 4) / D_m
    Z = (D_m ** 3 - d_i ** 3) / 6.0
    A = (math.pi / 4.0) * (D_m ** 2 - d_i ** 2)
    lam = D_m / t_c_m
    lam_limit = 0.07 * E_kpa / Fy_kpa
    return SectionProperties(
        D_m=D_m, t_c_m=t_c_m, S_m3=S, Z_m3=Z, A_m2=A,
        compact=lam <= lam_limit, slenderness_ratio=lam, slenderness_limit=lam_limit,
    )


@dataclass
class InteractionResult:
    equation: str  # "H1-1a" or "H1-1b"
    Pr_over_Pc: float
    Mr_over_Mc: float
    ratio: float
    passes: bool


def h1_interaction(
    Pr_kN: float, Mr_kNm: float, Fy_kpa: float, section: SectionProperties,
    phi_c: float = PHI_C, phi_b: float = PHI_B,
) -> InteractionResult:
    """AISC 360 Ch. H combined axial + flexure. Doc eq. 6.2.

    Pc = phi_c * Fy * A (conservatively using yield, not a separate Pn
         buckling reduction -- for a short embedded shaft this governs;
         for an exposed/unsupported length use a full column-buckling Pn).
    Mc = phi_b * Fy * Z  (compact round section).
    """
    Pc = phi_c * Fy_kpa * section.A_m2
    Mc = phi_b * Fy_kpa * section.Z_m3
    pr_pc = Pr_kN / Pc if Pc > 0 else float("inf")
    mr_mc = Mr_kNm / Mc if Mc > 0 else float("inf")

    if pr_pc >= 0.2:
        ratio = pr_pc + (8.0 / 9.0) * mr_mc
        eq = "H1-1a"
    else:
        ratio = pr_pc / 2.0 + mr_mc
        eq = "H1-1b"

    return InteractionResult(equation=eq, Pr_over_Pc=pr_pc, Mr_over_Mc=mr_mc,
                              ratio=ratio, passes=ratio <= 1.0)


def shear_check(Vu_kN: float, Fy_kpa: float, section: SectionProperties, phi_v: float = PHI_V) -> bool:
    """Vu <= phi_v * 0.6 * Fy * (A/2). Doc Section 6.2. Trivially satisfied
    for light poles; verify anyway."""
    Vn = 0.6 * Fy_kpa * (section.A_m2 / 2.0)
    return Vu_kN <= phi_v * Vn


def buckling_check_triggered(
    su_kpa: float | None = None,
    N60: float | None = None,
    continuous_weak_layer_m: float | None = None,
    exposed_or_scoured: bool = False,
) -> bool:
    """Doc Section 6.3 trigger logic: buckling check is required only if the
    pile passes through Su<25 kPa or N60<4 over a continuous layer >=1.5 m,
    or the shaft is exposed/scoured. Returns True if the check IS triggered
    (i.e. must be performed) -- always document the evaluation regardless
    of outcome.
    """
    if exposed_or_scoured:
        return True
    layer_long_enough = (continuous_weak_layer_m or 0.0) >= 1.5
    weak_su = su_kpa is not None and su_kpa < 25.0
    weak_n = N60 is not None and N60 < 4.0
    return layer_long_enough and (weak_su or weak_n)


def torsion_check(T_install_max_kNm: float, T_rated_kNm: float, phi_T: float = 0.90) -> bool:
    """Doc eq. 6.4: installation torque cap must never exceed the shaft/
    coupling manufacturer torsional rating (uncorroded section)."""
    return T_install_max_kNm <= phi_T * T_rated_kNm
