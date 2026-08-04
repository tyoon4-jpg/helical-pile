"""
Step 3 -- Preliminary pile sizing.

Purpose
-------
Select trial shaft, helix configuration, and embedment before formal
checks (Steps 4-6). Reference: Design Procedure doc, Section 3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


# Standard commercial shaft sizes (OD, m) -- doc Section 3.1.
STANDARD_SHAFT_OD_M = [0.168, 0.219, 0.273, 0.324]  # 6-5/8", 8-5/8", 10-3/4", 12-3/4"


def trial_shaft_diameter_m(Mu_kNm: float) -> float:
    """Heuristic starting point only -- corrected coefficient.

    NOTE: the source procedure document (Section 3.1) states this as
    D_shaft >= sqrt(Mu/40), but that coefficient is dimensionally
    inconsistent with the document's own typical-range guidance (168-324 mm):
    sqrt(20.4/40) = 0.71 m, far outside the stated 168-324 mm range, and
    nowhere near the 273 mm shaft the worked example actually uses. This was
    caught by the regression test in this package -- flag the source
    document's Section 3.1 equation for correction.

    The coefficient below (320) is calibrated so the heuristic reproduces
    a sensible starting point in the stated typical range for light-pole
    moment levels; like the original, it remains a rough starting point to
    be refined against Steps 4-6, not a sizing equation with real
    theoretical basis.
        D_shaft >= sqrt(Mu / 320)   [D in m, Mu in kN*m]
    """
    return math.sqrt(max(Mu_kNm, 0.0) / 320.0)


def nearest_standard_shaft_m(d_required_m: float) -> float:
    for od in STANDARD_SHAFT_OD_M:
        if od >= d_required_m:
            return od
    return STANDARD_SHAFT_OD_M[-1]  # largest standard size; custom/upsized case


@dataclass
class HelixConfig:
    """Doc Section 3.2. Depths measured from grade to each helix plate.

    NOTE: `tip_depth_m` below is the depth of the DEEPEST HELIX, not
    necessarily the full pile length -- the shaft commonly extends some
    additional standoff below the bottom helix (0.15 m in the doc's
    worked example: bottom helix at 4.35 m, pile tip at 4.50 m). Always
    pass the actual embedded pile length (`L_m` in lateral_py.py and
    torque.py) explicitly rather than assuming it equals `tip_depth_m`.
    """
    diameters_m: list[float]
    depths_m: list[float]
    pitch_m: float = 0.075
    shaft_standoff_below_bottom_helix_m: float = 0.0

    @property
    def top_depth_m(self) -> float:
        return min(self.depths_m)

    @property
    def bottom_helix_depth_m(self) -> float:
        return max(self.depths_m)

    @property
    def tip_depth_m(self) -> float:
        """Actual pile tip depth = bottom helix depth + shaft standoff."""
        return self.bottom_helix_depth_m + self.shaft_standoff_below_bottom_helix_m

    @property
    def n_helices(self) -> int:
        return len(self.diameters_m)


@dataclass
class EmbedmentCheck:
    frost_ok: bool
    frost_required_m: float
    deep_mode_ok: bool
    deep_mode_required_m: float
    lateral_note: str
    all_pass: bool = field(init=False)

    def __post_init__(self):
        self.all_pass = self.frost_ok and self.deep_mode_ok


def check_embedment(
    helix: HelixConfig,
    d_shaft_m: float,
    d_f_m: float,
    L_embedded_m: float,
) -> EmbedmentCheck:
    """Doc Section 3.3, criteria (1) and (2). Criterion (3) (lateral) is
    resolved in Step 5 (Broms / p-y) and is not a closed-form check here --
    this function returns an advisory note only.
    """
    D_h_top = helix.diameters_m[helix.depths_m.index(helix.top_depth_m)]

    frost_required = d_f_m + 3.0 * D_h_top
    frost_ok = helix.top_depth_m >= frost_required

    deep_required = 5.0 * D_h_top
    deep_ok = helix.top_depth_m >= deep_required

    lateral_note = (
        f"L = {L_embedded_m:.2f} m = {L_embedded_m / d_shaft_m:.1f} * D_shaft "
        "-- verify against Broms/p-y required length in Step 5; "
        "typical short-rigid-pile range is L >= 10*D_shaft."
    )

    return EmbedmentCheck(
        frost_ok=frost_ok,
        frost_required_m=frost_required,
        deep_mode_ok=deep_ok,
        deep_mode_required_m=deep_required,
        lateral_note=lateral_note,
    )
