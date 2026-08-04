"""
Step 7 -- Corrosion design (design-life sacrificial thickness).

Purpose
-------
Combine galvanizing + sacrificial steel so the Step 6 checks remain valid
at end of life. Reference: Design Procedure doc, Section 7.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CorrosionResult:
    zinc_life_yr: float
    t_sac_mm: float
    t_corroded_mm: float
    classification: str


def sacrificial_thickness_mm(
    t_zn_um: float,
    r_zn_um_per_yr: float,
    r_s_um_per_yr: float,
    design_life_yr: float,
) -> tuple[float, float]:
    """Doc eq. 7.2.
        t_zn_life = t_zn / r_zn                    [yr]
        t_sac     = r_s * (T_life - t_zn_life)      [mm], per exposed face

    Returns (zinc_life_yr, t_sac_mm). If zinc life exceeds the design life,
    t_sac is clamped to zero (no bare-steel exposure occurs).
    """
    zinc_life_yr = t_zn_um / r_zn_um_per_yr
    remaining_yr = max(design_life_yr - zinc_life_yr, 0.0)
    t_sac_mm = r_s_um_per_yr * remaining_yr / 1000.0
    return zinc_life_yr, t_sac_mm


def corroded_wall_mm(t_nominal_mm: float, t_sac_mm: float, both_faces: bool = False) -> float:
    """t_c = t - t_sac (outer face only, closed/sealed pipe -- default) or
    t - 2*t_sac if the section is open/vented and both faces corrode.
    Doc Section 7.2. This is the value that MUST feed structural.py."""
    loss = t_sac_mm * (2 if both_faces else 1)
    return t_nominal_mm - loss


def classify_corrosivity(
    resistivity_ohm_cm: float,
    ph: float,
    design_life_yr: float,
    ac358_baseline_yr: float = 50.0,
) -> str:
    """Doc Section 7.1 screening logic (simplified). AC358 non-aggressive
    thresholds should be confirmed against the current report [verify
    AC358 Sec.3.x thresholds] -- this is a conservative default screen.
    """
    if resistivity_ohm_cm < 1000.0 or ph < 5.5:
        return "severely corrosive -- cathodic protection or epoxy required; " \
               "confirm helical piles are permitted per AC358 in this soil"
    passes_screen = resistivity_ohm_cm >= 2000.0 and 5.5 <= ph <= 10.0
    if passes_screen and design_life_yr <= ac358_baseline_yr:
        return "non-aggressive (screening basis)"
    return "moderately corrosive design case -- explicit sacrificial-thickness " \
           "calculation required (screen passes, but life exceeds AC358 baseline " \
           "and/or life-safety-adjacent application)"


def design_corrosion(
    t_nominal_mm: float,
    t_zn_um: float,
    r_zn_um_per_yr: float,
    r_s_um_per_yr: float,
    design_life_yr: float,
    resistivity_ohm_cm: float,
    ph: float,
    both_faces: bool = False,
) -> CorrosionResult:
    """Convenience wrapper running the full Step 7 sequence."""
    zinc_life, t_sac = sacrificial_thickness_mm(t_zn_um, r_zn_um_per_yr, r_s_um_per_yr, design_life_yr)
    t_c = corroded_wall_mm(t_nominal_mm, t_sac, both_faces=both_faces)
    classification = classify_corrosivity(resistivity_ohm_cm, ph, design_life_yr)
    return CorrosionResult(
        zinc_life_yr=zinc_life, t_sac_mm=t_sac, t_corroded_mm=t_c,
        classification=classification,
    )
