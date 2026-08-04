"""
Step 4 -- Axial capacity check (compression and tension / frost uplift).

Purpose
-------
Verify axial geotechnical capacity by both the individual-bearing and
cylindrical-shear methods; the lesser governs. Reference: Design Procedure
doc, Section 4. FS = 2.0 on ultimate geotechnical capacity (both directions).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

FS_AXIAL = 2.0  # doc Section 4, IBC 2021 Sec.1810 / AC358 basis


def helix_net_area_m2(D_h_m: float, D_shaft_m: float) -> float:
    """A_h = pi/4 * (D_h^2 - D_shaft^2). Doc eq. 4.1."""
    return math.pi / 4.0 * (D_h_m ** 2 - D_shaft_m ** 2)


def adhesion_factor(su_kpa: float) -> float:
    """alpha (API): 1.0 at Su<=25 kPa, linearly down to 0.5 at Su>=70 kPa. Doc eq. 4.1."""
    if su_kpa <= 25.0:
        return 1.0
    if su_kpa >= 70.0:
        return 0.5
    return 1.0 + (su_kpa - 25.0) * (0.5 - 1.0) / (70.0 - 25.0)


# --------------------------------------------------------------------------
# 4.1 Individual bearing method (clay), ultimate
# --------------------------------------------------------------------------

def individual_bearing_compression_kN(
    helix_diams_m: list[float],
    D_shaft_m: float,
    su_kpa: float,
    L_eff_m: float,
    Nc: float = 9.0,
    alpha_override: float | None = None,
) -> float:
    """Qu = sum(A_h,i * 9*Su) + alpha*Su*pi*D_shaft*L_eff. Doc eq. 4.1 (clay).

    `alpha_override`: the doc's Section 4.1 correlation (linear ramp,
    alpha=1.0 at Su<=25 kPa down to alpha=0.5 at Su>=70 kPa) is a common
    simplification of the API adhesion-factor curve, which is not actually
    linear -- real API-derived alpha values typically drop faster than a
    straight line between those anchor points. The worked example (Section
    11.4) uses a conservative rounded alpha=0.5 at Su=50 kPa rather than
    the ~0.72 the linear ramp would give. Pass alpha_override to reproduce
    a specific project's chosen basis (lab-derived, product literature, or
    a conservative round number) instead of the built-in linear ramp.
    """
    helix_term = sum(helix_net_area_m2(dh, D_shaft_m) * Nc * su_kpa for dh in helix_diams_m)
    alpha = alpha_override if alpha_override is not None else adhesion_factor(su_kpa)
    shaft_term = alpha * su_kpa * math.pi * D_shaft_m * L_eff_m
    return helix_term + shaft_term


def individual_bearing_tension_kN(
    helix_diams_m: list[float],
    D_shaft_m: float,
    su_kpa: float,
    L_eff_m: float,
    Nc: float = 9.0,
    include_shaft_adhesion: bool = False,
) -> float:
    """Tension version: helix areas in uplift bearing only; excludes tip term
    and all frost-zone contact. Shaft adhesion below d_f may optionally be
    included (conservative default: excluded, per worked example). Doc 4.1.
    """
    helix_term = sum(helix_net_area_m2(dh, D_shaft_m) * Nc * su_kpa for dh in helix_diams_m)
    if not include_shaft_adhesion:
        return helix_term
    alpha = adhesion_factor(su_kpa)
    return helix_term + alpha * su_kpa * math.pi * D_shaft_m * L_eff_m


# --------------------------------------------------------------------------
# 4.2 Cylindrical shear method, ultimate
# --------------------------------------------------------------------------

def cylindrical_shear_compression_kN(
    D_h_bottom_m: float,
    D_shaft_m: float,
    su_kpa: float,
    D_h_avg_m: float,
    L_c_m: float,
    L_eff_m: float,
    Nc: float = 9.0,
) -> float:
    """Qu = A_h,bottom*qult,bottom + Su*pi*D_h_avg*L_c + alpha*Su*pi*D_shaft*L_eff.
    Doc eq. 4.2 (compression)."""
    bottom_bearing = helix_net_area_m2(D_h_bottom_m, D_shaft_m) * Nc * su_kpa
    cylinder_shear = su_kpa * math.pi * D_h_avg_m * L_c_m
    alpha = adhesion_factor(su_kpa)
    shaft_term = alpha * su_kpa * math.pi * D_shaft_m * L_eff_m
    return bottom_bearing + cylinder_shear + shaft_term


# --------------------------------------------------------------------------
# 4.3 Frost-heave uplift demand
# --------------------------------------------------------------------------

def frost_uplift_demand_kN(tau_ad_kpa: float, D_shaft_m: float, d_f_m: float) -> float:
    """T_frost = tau_ad * pi * D_shaft * d_f. Doc eq. 4.3."""
    return tau_ad_kpa * math.pi * D_shaft_m * d_f_m


# --------------------------------------------------------------------------
# 4.4 Acceptance
# --------------------------------------------------------------------------

@dataclass
class AxialCheckResult:
    Qu_individual_kN: float
    Qu_cylindrical_kN: float
    Qu_governing_kN: float
    demand_kN: float
    FS_actual: float
    FS_required: float
    passes: bool
    governing_method: str


def check_compression(
    Qu_individual_kN: float,
    Qu_cylindrical_kN: float,
    P_max_kN: float,
    FS: float = FS_AXIAL,
) -> AxialCheckResult:
    governing = min(Qu_individual_kN, Qu_cylindrical_kN)
    method = "individual bearing" if Qu_individual_kN <= Qu_cylindrical_kN else "cylindrical shear"
    fs_actual = governing / P_max_kN if P_max_kN > 0 else float("inf")
    return AxialCheckResult(
        Qu_individual_kN=Qu_individual_kN,
        Qu_cylindrical_kN=Qu_cylindrical_kN,
        Qu_governing_kN=governing,
        demand_kN=P_max_kN,
        FS_actual=fs_actual,
        FS_required=FS,
        passes=fs_actual >= FS,
        governing_method=method,
    )


def check_tension(
    Tu_individual_kN: float,
    Tu_cylindrical_kN: float,
    T_frost_net_kN: float,
    FS: float = FS_AXIAL,
) -> AxialCheckResult:
    governing = min(Tu_individual_kN, Tu_cylindrical_kN)
    method = "individual bearing" if Tu_individual_kN <= Tu_cylindrical_kN else "cylindrical shear"
    fs_actual = governing / T_frost_net_kN if T_frost_net_kN > 0 else float("inf")
    return AxialCheckResult(
        Qu_individual_kN=Tu_individual_kN,
        Qu_cylindrical_kN=Tu_cylindrical_kN,
        Qu_governing_kN=governing,
        demand_kN=T_frost_net_kN,
        FS_actual=fs_actual,
        FS_required=FS,
        passes=fs_actual >= FS,
        governing_method=method,
    )
