"""
Step 5 -- Lateral and moment capacity check.

Purpose
-------
The governing check for a light-pole helical pile. Verify ultimate
lateral/moment stability (Broms, preliminary) and serviceability
deflection/rotation (p-y beam-on-nonlinear-Winkler-foundation, final).
Reference: Design Procedure doc, Section 5.

The p-y solver here is the same formulation LPILE solves: a beam-column on
nonlinear soil springs, iterated to convergence via secant stiffness. It
was cross-validated in the worked example (Section 11.5) against an
independent closed-form Broms solution, agreeing within ~3%. Any change to
this module should be checked against `tests/test_worked_example_12m.py`
before being trusted.

FS = 2.0 on Broms ultimate lateral resistance for preliminary sizing.
Final acceptance is by p-y serviceability (deflection/rotation limits) and
by p-y ultimate pushover with FS >= 2.0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

FS_LATERAL_PRELIM = 2.0   # Broms, doc Section 5.2
FS_PUSHOVER = 2.0         # p-y pushover, doc Section 5.3
SERVICE_Y_LIMIT_M = 0.012   # A16 default, confirm with owner
SERVICE_THETA_LIMIT_DEG = 0.5  # A16 default, confirm with owner


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

@dataclass
class ClaySoil:
    """Matlock soft-clay static p-y parameters. Doc Section 5.3 / 11.5.2."""
    su_kpa: float
    gamma_kNm3: float          # total unit weight above GWT
    gamma_sub_kNm3: float      # submerged unit weight below GWT
    gwt_depth_m: float
    eps50: float
    frost_depth_m: float       # p is zeroed for z <= frost_depth_m (winter case)
    J: float = 0.5


@dataclass
class PileSection:
    """Shaft properties for the beam-column model. Use the CORRODED wall
    thickness (Step 7 output), never nominal, for design-life checks."""
    D_m: float
    t_m: float
    E_kpa: float = 200e6  # 200 GPa, steel

    @property
    def I_m4(self) -> float:
        d_i = self.D_m - 2 * self.t_m
        return math.pi / 64.0 * (self.D_m ** 4 - d_i ** 4)

    @property
    def EI_kNm2(self) -> float:
        return self.E_kpa * self.I_m4


@dataclass
class PySolution:
    z_m: np.ndarray
    y_m: np.ndarray
    theta_rad: np.ndarray
    M_kNm: np.ndarray
    converged: bool

    @property
    def y_gl_mm(self) -> float:
        return self.y_m[0] * 1000.0

    @property
    def theta_gl_deg(self) -> float:
        return math.degrees(self.theta_rad[0])

    @property
    def M_max_kNm(self) -> float:
        return float(np.max(np.abs(self.M_kNm)))

    @property
    def M_max_depth_m(self) -> float:
        return float(self.z_m[np.argmax(np.abs(self.M_kNm))])

    def toe_kickback_depths_m(self) -> list[float]:
        """Depths where the deflected shape crosses zero -- doc 5.3-4:
        presence of a crossing (toe kick-back) confirms embedment adequacy;
        an empty list means the toe is still translating -> lengthen the pile.
        """
        s = np.sign(self.y_m)
        idx = np.where(np.diff(s) != 0)[0]
        return [float(self.z_m[i]) for i in idx]


# --------------------------------------------------------------------------
# 5.2 Broms method -- free-head short rigid pile in clay (preliminary)
# --------------------------------------------------------------------------

def broms_ultimate_clay_kN(
    su_kpa: float,
    D_shaft_m: float,
    L_m: float,
    e_m: float,
    d_f_m: float,
    tol: float = 1e-6,
    max_iter: int = 200,
) -> float:
    """Solve for Hu given L (doc eq. 5.2), free-head short rigid pile, clay.

        z0 = max(1.5*D_shaft, d_f)
        f  = Hu / (9*Su*D_shaft)
        M_max = Hu*(e + z0 + 0.5*f) = 2.25*Su*D_shaft*g^2
        L  = z0 + f + g

    Solved by bisection on Hu such that the geometry closure L = z0+f+g
    is satisfied for the given embedded length L.
    """
    z0 = max(1.5 * D_shaft_m, d_f_m)
    avail = L_m - z0
    if avail <= 0:
        raise ValueError("Embedded length does not clear the exclusion depth z0.")

    def g_of_Hu(Hu: float) -> float:
        f = Hu / (9.0 * su_kpa * D_shaft_m)
        Mmax = Hu * (e_m + z0 + 0.5 * f)
        g = math.sqrt(max(Mmax, 0.0) / (2.25 * su_kpa * D_shaft_m))
        return f + g - avail

    lo, hi = 1e-6, 1.0
    while g_of_Hu(hi) < 0 and hi < 1e7:
        hi *= 2.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        val = g_of_Hu(mid)
        if abs(val) < tol:
            return mid
        if val > 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------
# 5.3 p-y method -- Matlock soft-clay curves + FD beam-spring solver
# --------------------------------------------------------------------------

def sigma_v_eff_kpa(z_m: float, soil: ClaySoil) -> float:
    if z_m <= soil.gwt_depth_m:
        return soil.gamma_kNm3 * z_m
    return soil.gamma_kNm3 * soil.gwt_depth_m + soil.gamma_sub_kNm3 * (z_m - soil.gwt_depth_m)


def matlock_pu(z_m: float, D_shaft_m: float, soil: ClaySoil) -> tuple[float, float]:
    """pu(z) = Np*Su*D ; Np = min(3 + sigma'v/Su + J*z/D, 9). Doc eq. 5.3.2.
    Returns (pu_kNm, Np)."""
    Np = min(3.0 + sigma_v_eff_kpa(z_m, soil) / soil.su_kpa + soil.J * z_m / D_shaft_m, 9.0)
    return Np * soil.su_kpa * D_shaft_m, Np


def matlock_p_of_y(z_m: float, y_m: float, D_shaft_m: float, soil: ClaySoil) -> float:
    """p(y) = 0.5*pu*(y/y50)^(1/3) for |y| < 8*y50, else pu. Doc eq. 5.3.2.
    Zeroed within the frost depth (winter load case)."""
    if z_m <= soil.frost_depth_m:
        return 0.0
    pu, _ = matlock_pu(z_m, D_shaft_m, soil)
    y50 = 2.5 * soil.eps50 * D_shaft_m
    ay = abs(y_m)
    if ay >= 8 * y50:
        p = pu
    else:
        p = 0.5 * pu * (ay / y50) ** (1.0 / 3.0)
    return p if y_m >= 0 else -p


def solve_py(
    V_kN: float,
    M_kNm: float,
    pile: PileSection,
    soil: ClaySoil,
    L_m: float,
    n_elements: int = 180,
    tol_m: float = 1e-9,
    max_iter: int = 800,
) -> PySolution | None:
    """Beam-on-nonlinear-Winkler-foundation solve, free head.

    Sign convention: (V, M) must be a SIGN-CONSISTENT free-head pair -- i.e.
    moment and shear deflect the head in the same direction, which is the
    governing sense for a pole load applied at eccentricity e = M/V. Pass M
    with the sign that makes physical sense for your load case; this
    function does not second-guess the sign you provide.

    Returns None if the discretized system does not converge (a signal of
    incipient collapse under a pushover load -- see `pushover`).
    """
    EI = pile.EI_kNm2
    h = L_m / n_elements
    nn = n_elements + 1
    ndof = 2 * nn
    z = np.linspace(0.0, L_m, nn)

    k_elem = EI / h ** 3 * np.array([
        [12, 6 * h, -12, 6 * h],
        [6 * h, 4 * h * h, -6 * h, 2 * h * h],
        [-12, -6 * h, 12, -6 * h],
        [6 * h, 2 * h * h, -6 * h, 4 * h * h],
    ])
    K_beam = np.zeros((ndof, ndof))
    for e in range(n_elements):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K_beam[np.ix_(idx, idx)] += k_elem

    F = np.zeros(ndof)
    F[0] = V_kN
    F[1] = M_kNm

    trib = np.full(nn, h)
    trib[0] = h / 2.0
    trib[-1] = h / 2.0

    y = np.full(nn, 1e-5)
    u = None
    converged = False
    for _ in range(max_iter):
        K = K_beam.copy()
        for i in range(nn):
            yi = y[i] if abs(y[i]) > 1e-9 else 1e-9
            p = matlock_p_of_y(z[i], yi, pile.D_m, soil)
            ks = abs(p / yi) * trib[i]
            K[2 * i, 2 * i] += ks
        try:
            u = np.linalg.solve(K, F)
        except np.linalg.LinAlgError:
            return None
        y_new = u[0::2]
        delta = np.max(np.abs(y_new - y))
        y = 0.5 * y + 0.5 * y_new
        if delta < tol_m:
            converged = True
            y = y_new
            break

    if u is None:
        return None
    theta = u[1::2]

    M_node = np.zeros(nn)
    cnt = np.zeros(nn)
    for e in range(n_elements):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        ue = u[idx]
        fe = k_elem @ ue
        M_node[e] += -fe[1]
        cnt[e] += 1
        M_node[e + 1] += fe[3]
        cnt[e + 1] += 1
    M_node /= np.maximum(cnt, 1)

    return PySolution(z_m=z, y_m=y, theta_rad=theta, M_kNm=M_node, converged=converged)


# --------------------------------------------------------------------------
# 5.3 acceptance + pushover
# --------------------------------------------------------------------------

@dataclass
class ServiceabilityResult:
    solution: PySolution
    y_limit_m: float
    theta_limit_deg: float
    y_passes: bool
    theta_passes: bool

    @property
    def passes(self) -> bool:
        return self.y_passes and self.theta_passes


def check_serviceability(
    solution: PySolution,
    y_limit_m: float = SERVICE_Y_LIMIT_M,
    theta_limit_deg: float = SERVICE_THETA_LIMIT_DEG,
) -> ServiceabilityResult:
    """Doc acceptance, Section 5.3: y_gl <= limit AND theta_gl <= limit."""
    y_pass = abs(solution.y_gl_mm) / 1000.0 <= y_limit_m
    th_pass = abs(solution.theta_gl_deg) <= theta_limit_deg
    return ServiceabilityResult(
        solution=solution,
        y_limit_m=y_limit_m,
        theta_limit_deg=theta_limit_deg,
        y_passes=y_pass,
        theta_passes=th_pass,
    )


@dataclass
class PushoverPoint:
    lam: float
    solution: PySolution | None


@dataclass
class PushoverResult:
    points: list[PushoverPoint]
    lambda_ult: float  # last converged multiplier before collapse

    def passes(self, fs_required: float = FS_PUSHOVER) -> bool:
        return self.lambda_ult >= fs_required


def pushover(
    V_u_kN: float,
    M_u_kNm: float,
    pile: PileSection,
    soil: ClaySoil,
    L_m: float,
    lambdas: list[float] | None = None,
    y_collapse_m: float = 0.20,
) -> PushoverResult:
    """Scale the strength load pair by lambda until the solver fails to
    converge or head deflection runs away -- doc Section 5.3-3/5.3.5.
    lambda_ult brackets the ultimate pushover capacity factor; compare
    against the independent Broms FS as a cross-check (doc 11.5.5).
    """
    if lambdas is None:
        lambdas = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
                   9.5, 10.0, 10.5, 11.0, 12.0]

    points: list[PushoverPoint] = []
    lambda_ult = 0.0
    for lam in lambdas:
        sol = solve_py(V_u_kN * lam, M_u_kNm * lam, pile, soil, L_m)
        if sol is not None and sol.converged and abs(sol.y_gl_mm) / 1000.0 < y_collapse_m:
            points.append(PushoverPoint(lam=lam, solution=sol))
            lambda_ult = lam
        else:
            points.append(PushoverPoint(lam=lam, solution=None))
            break
    return PushoverResult(points=points, lambda_ult=lambda_ult)
