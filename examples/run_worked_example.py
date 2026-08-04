"""
Run the full 10-step design procedure end-to-end on the 12 m pole /
medium-stiff-clay worked example, printing a readable report to the
console.

Usage:
    python examples/run_worked_example.py

This is the fastest way to see the calc engine actually work before
building any UI on top of it. Every section below corresponds to a
numbered step in the design procedure document.
"""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")  # see README: p-y solver + many-core OpenBLAS

from helical_pile_design import loads, geotech, sizing, axial, structural, corrosion, torque, qaqc
from helical_pile_design.lateral_py import (
    ClaySoil, PileSection, solve_py, broms_ultimate_clay_kN, pushover, check_serviceability,
)


def hr(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def main() -> None:
    # ---------------------------------------------------------------
    # STEP 1 -- Loads
    # ---------------------------------------------------------------
    hr("STEP 1 -- Load determination")
    pole = loads.PoleGeometry(height_m=12.0, base_diam_m=0.25, top_diam_m=0.10,
                               projected_area_m2=2.10, weight_kN=1.50, Cd=0.50)
    lum = loads.LuminaireLoad(epa_m2=0.50, weight_kN=0.25)
    wind_strength = loads.WindEnvironment(V_ms=51.4, Kz_top=1.04, Kz_centroid=1.00)
    wind_service = loads.service_wind_environment(wind_strength)

    strength = loads.base_reactions(pole, lum, wind_strength, dead_load_factor=1.25)
    service = loads.base_reactions(pole, lum, wind_service)
    print(f"Strength: V_u={strength.V_kN:.2f} kN, M_u={strength.M_kNm:.2f} kN*m, "
          f"P_u={strength.P_kN:.2f} kN, e={strength.e_m:.2f} m")
    print(f"Service:  V_s={service.V_kN:.2f} kN, M_s={service.M_kNm:.2f} kN*m")

    # ---------------------------------------------------------------
    # STEP 2 -- Geotechnical parameterization
    # ---------------------------------------------------------------
    hr("STEP 2 -- Geotechnical parameterization")
    su = 50.0  # kPa, given directly for this example (lab/CPT basis assumed available)
    eps50 = geotech.eps50_from_su(su)
    print(f"Su = {su} kPa, eps50 (Matlock band) = {eps50}")

    # ---------------------------------------------------------------
    # STEP 3 -- Preliminary sizing
    # ---------------------------------------------------------------
    hr("STEP 3 -- Preliminary pile sizing")
    d_shaft = sizing.nearest_standard_shaft_m(sizing.trial_shaft_diameter_m(strength.M_kNm))
    helix = sizing.HelixConfig(diameters_m=[0.450, 0.450], depths_m=[3.00, 4.35], shaft_standoff_below_bottom_helix_m=0.15)
    d_f = 1.2
    embed = sizing.check_embedment(helix, d_shaft, d_f, helix.tip_depth_m)
    print(f"Trial shaft: {d_shaft*1000:.0f} mm OD, helices at {helix.depths_m} m, "
          f"tip at {helix.tip_depth_m} m")
    print(f"Embedment checks pass: {embed.all_pass} "
          f"(frost req={embed.frost_required_m:.2f} m, deep-mode req={embed.deep_mode_required_m:.2f} m)")

    # ---------------------------------------------------------------
    # STEP 4 -- Axial capacity
    # ---------------------------------------------------------------
    hr("STEP 4 -- Axial capacity (compression / tension)")
    Qu = axial.individual_bearing_compression_kN(helix.diameters_m, d_shaft, su, L_eff_m=1.35, alpha_override=0.5)
    comp = axial.check_compression(Qu, Qu * 1.4, P_max_kN=strength.P_kN)
    print(f"Compression: Qu={comp.Qu_governing_kN:.1f} kN ({comp.governing_method}), "
          f"FS={comp.FS_actual:.1f} (req {comp.FS_required}) -> {'PASS' if comp.passes else 'FAIL'}")

    tau_ad_sleeve = 20.0
    T_frost = axial.frost_uplift_demand_kN(tau_ad_sleeve, d_shaft, d_f)
    Tu = axial.individual_bearing_tension_kN(helix.diameters_m, d_shaft, su, L_eff_m=0.0)
    tens = axial.check_tension(Tu, Tu * 1.3, T_frost)
    print(f"Tension:     T_frost={T_frost:.1f} kN, Tu={tens.Qu_governing_kN:.1f} kN, "
          f"FS={tens.FS_actual:.1f} (req {tens.FS_required}) -> {'PASS' if tens.passes else 'FAIL'}")

    # ---------------------------------------------------------------
    # STEP 5 -- Lateral / moment (the governing check)
    # ---------------------------------------------------------------
    hr("STEP 5 -- Lateral and moment capacity (governing check)")
    t_c_mm = 8.3  # corroded wall, computed in Step 7 below -- shown here for the p-y run
    pile_section = PileSection(D_m=d_shaft, t_m=t_c_mm / 1000.0)
    soil = ClaySoil(su_kpa=su, gamma_kNm3=18.5, gamma_sub_kNm3=18.5 - 9.81,
                     gwt_depth_m=3.0, eps50=eps50, frost_depth_m=d_f)

    Hu = broms_ultimate_clay_kN(su, d_shaft, L_m=helix.tip_depth_m, e_m=strength.e_m, d_f_m=d_f)
    print(f"Broms (preliminary): Hu={Hu:.1f} kN, FS={Hu/strength.V_kN:.1f} (req 2.0)")

    sol_service = solve_py(service.V_kN, -service.M_kNm, pile_section, soil, L_m=helix.tip_depth_m)
    svc = check_serviceability(sol_service)
    print(f"p-y service:  y_gl={sol_service.y_gl_mm:.2f} mm, theta_gl={abs(sol_service.theta_gl_deg):.3f} deg "
          f"-> {'PASS' if svc.passes else 'FAIL'}")

    sol_strength = solve_py(strength.V_kN, -strength.M_kNm, pile_section, soil, L_m=helix.tip_depth_m)
    print(f"p-y strength: y_gl={sol_strength.y_gl_mm:.2f} mm, theta_gl={abs(sol_strength.theta_gl_deg):.3f} deg, "
          f"M_max={sol_strength.M_max_kNm:.1f} kN*m @ z={sol_strength.M_max_depth_m:.2f} m")

    po = pushover(strength.V_kN, -strength.M_kNm, pile_section, soil, L_m=helix.tip_depth_m)
    print(f"Pushover: lambda_ult ~= {po.lambda_ult:.1f} -> {'PASS' if po.passes() else 'FAIL'} (req 2.0)")

    # ---------------------------------------------------------------
    # STEP 6 -- Structural (AISC 360)
    # ---------------------------------------------------------------
    hr("STEP 6 -- Shaft structural checks (AISC 360, corroded section)")
    Fy = 345e3  # kPa
    section = structural.section_properties(d_shaft, t_c_mm / 1000.0, Fy)
    print(f"Section: S={section.S_m3*1e9:.0f} mm^3-equiv, compact={section.compact}")
    h1 = structural.h1_interaction(strength.P_kN, sol_strength.M_max_kNm, Fy, section)
    print(f"H1 interaction ({h1.equation}): ratio={h1.ratio:.3f} -> {'PASS' if h1.passes else 'FAIL'}")

    # ---------------------------------------------------------------
    # STEP 7 -- Corrosion
    # ---------------------------------------------------------------
    hr("STEP 7 -- Corrosion design (75-year life)")
    corr = corrosion.design_corrosion(
        t_nominal_mm=9.3, t_zn_um=100.0, r_zn_um_per_yr=4.0, r_s_um_per_yr=20.0,
        design_life_yr=75.0, resistivity_ohm_cm=3000.0, ph=6.5,
    )
    print(f"Zinc life={corr.zinc_life_yr:.0f} yr, t_sac={corr.t_sac_mm:.2f} mm, "
          f"t_corroded={corr.t_corroded_mm:.2f} mm")
    print(f"Classification: {corr.classification}")

    # ---------------------------------------------------------------
    # STEP 9 -- Torque
    # ---------------------------------------------------------------
    hr("STEP 9 -- Installation torque specification")
    P_req = torque.required_ultimate_axial_kN(2.0 * strength.P_kN, 2.0 * T_frost)
    Kt = 7.0
    T_min = torque.t_min_kNm(P_req, Kt)
    print(f"Required ultimate axial={P_req:.1f} kN, Kt={Kt} m^-1 [ASSUMED -- validate], "
          f"T_min={T_min:.2f} kN*m")

    # ---------------------------------------------------------------
    # STEP 10 -- QA/QC triggers
    # ---------------------------------------------------------------
    hr("STEP 10 -- QA/QC and load test triggers")
    trig_inputs = qaqc.LoadTestTriggerInputs(
        kt_established_by_ac358=False,
        frost_uplift_relies_on_assumed_values=True,
        py_params_from_lab_or_cpt=False,
        predicted_y_over_limit_ratio=abs(sol_service.y_gl_mm) / 1000.0 / svc.y_limit_m,
        n_production_piles=40,
        variable_or_unfamiliar_soils=False,
    )
    triggers = qaqc.evaluate_load_test_triggers(trig_inputs)
    print(f"Triggered tests: {sorted(triggers.triggered_tests)}")
    for reason in triggers.reasons:
        print(f"  - {reason}")

    hr("RESULT")
    all_pass = comp.passes and tens.passes and svc.passes and po.passes() and h1.passes
    print(f"Overall: {'PASSES all implemented checks' if all_pass else 'ONE OR MORE CHECKS FAILED'}")


if __name__ == "__main__":
    main()
