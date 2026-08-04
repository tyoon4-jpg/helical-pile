"""
Step 2 -- Geotechnical parameterization.

Purpose
-------
Convert field data (SPT/CPT, lab) into design soil parameters.
Reference: Design Procedure doc, Section 2.

These are preliminary correlations. Prefer lab UU/CU or CPT-derived
parameters over SPT correlation wherever available -- and flag which basis
was used, since Step 10 (QA/QC) triggers a lateral load test when p-y
inputs are correlation-only.
"""
from __future__ import annotations

from dataclasses import dataclass


# --------------------------------------------------------------------------
# 2.1 Cohesive soils
# --------------------------------------------------------------------------

def su_from_n60_kpa(N60: float) -> float:
    """Su ~= 6 * N60 [kPa]. Preliminary only -- prefer lab/CPT. Doc eq. 2.1."""
    return 6.0 * N60


def su_from_cpt_kpa(qt_kpa: float, sigma_v0_kpa: float, Nkt: float = 14.0) -> float:
    """Su = (qt - sigma_v0) / Nkt, Nkt = 12-16 (CPT). Doc eq. 2.1."""
    return (qt_kpa - sigma_v0_kpa) / Nkt


def eps50_from_su(su_kpa: float) -> float:
    """Matlock strain-at-half-stress vs. undrained shear strength band. Doc eq. 2.1.

    0.02   : soft,   Su < 25 kPa
    0.01   : medium, 25 <= Su <= 50 kPa
    0.005-0.007 : stiff, Su > 50 kPa (use 0.007 unless site data indicate otherwise)
    """
    if su_kpa < 25.0:
        return 0.020
    if su_kpa <= 50.0:
        return 0.010
    return 0.007


# --------------------------------------------------------------------------
# 2.2 Cohesionless soils
# --------------------------------------------------------------------------

def phi_from_n60_deg(N60: float) -> float:
    """Peck/Hanson correlation, preliminary. Doc eq. 2.2.

    phi' ~= 27.1 + 0.3*N60 - 0.00054*N60^2
    """
    return 27.1 + 0.3 * N60 - 0.00054 * N60 ** 2


# --------------------------------------------------------------------------
# 2.3 Design soil profile record
# --------------------------------------------------------------------------

@dataclass
class SoilLayer:
    """One layer of the signed design soil profile (doc Section 2.3).

    For clay: set su_kpa, leave phi_deg=None.
    For sand: set phi_deg, leave su_kpa=None.
    """
    top_depth_m: float
    bottom_depth_m: float
    gamma_kNm3: float
    su_kpa: float | None = None
    phi_deg: float | None = None
    eps50: float | None = None
    basis: str = "SPT correlation"   # "SPT correlation" | "lab UU/CU" | "CPT" | "lab + CPT"

    def is_clay(self) -> bool:
        return self.su_kpa is not None


@dataclass
class SoilProfile:
    layers: list[SoilLayer]
    gwt_depth_m: float

    def weakest_layer_in_zone(self, zone_bottom_m: float) -> SoilLayer:
        """Doc rule 2.3-1: use the weakest credible layer within the lateral
        influence zone (top ~10 shaft diameters) for lateral design."""
        candidates = [l for l in self.layers if l.top_depth_m < zone_bottom_m]
        if not candidates:
            raise ValueError("No layers found within the specified zone.")
        clay_layers = [l for l in candidates if l.is_clay()]
        if clay_layers:
            return min(clay_layers, key=lambda l: l.su_kpa)
        return min(candidates, key=lambda l: l.phi_deg)

    def any_lab_or_cpt_basis(self) -> bool:
        """Feeds the Step 10 QA/QC trigger: True only if at least one layer
        governing the design is backed by lab or CPT data, not SPT alone."""
        return any(l.basis != "SPT correlation" for l in self.layers)
