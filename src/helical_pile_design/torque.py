"""
Step 9 -- Installation torque specification.

Purpose
-------
Set dual termination criteria (minimum torque AND minimum depth) and
define the Kt verification logic. Torque verifies AXIAL capacity only --
it can never waive the minimum embedment depth from Steps 3/5.
Reference: Design Procedure doc, Section 9.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TorqueSpec:
    T_min_kNm: float
    tip_depth_min_m: float
    top_helix_depth_min_m: float
    T_rated_kNm: float
    Kt_source: str  # "AC358 report" | "site load test" | "ASSUMED -- validate before production"


def required_ultimate_axial_kN(P_compression_ult_kN: float, T_frost_ult_kN: float) -> float:
    """max(FS*P_compression, FS*T_frost_net) -- the FS multiplication is
    expected to already be applied by the caller (axial.py results carry
    FS separately); this just takes the governing ultimate demand.
    Doc eq. 9.2 (1)."""
    return max(P_compression_ult_kN, T_frost_ult_kN)


def t_min_kNm(P_req_ultimate_kN: float, Kt_per_m: float) -> float:
    """T_min = (FS * P_req) / Kt. Doc eq. 9.2 (1). Kt must come from an
    AC358 product evaluation report or a site-specific load test -- never
    assumed from generic tables for large-diameter shafts without
    validation (doc Section 9.1)."""
    return P_req_ultimate_kN / Kt_per_m


@dataclass
class TerminationCheck:
    torque_ok: bool
    depth_ok: bool
    cap_ok: bool

    @property
    def all_pass(self) -> bool:
        return self.torque_ok and self.depth_ok and self.cap_ok


def check_termination(
    T_avg_kNm: float, T_min_kNm_: float,
    tip_depth_m: float, tip_depth_min_m: float,
    T_rated_kNm: float,
) -> TerminationCheck:
    """Doc Section 9.2, ALL THREE must be satisfied:
        (1) T_avg >= T_min
        (2) tip depth >= specified minimum (torque can never waive this)
        (3) T <= T_rated at all times
    """
    return TerminationCheck(
        torque_ok=T_avg_kNm >= T_min_kNm_,
        depth_ok=tip_depth_m >= tip_depth_min_m,
        cap_ok=T_avg_kNm <= T_rated_kNm,
    )
