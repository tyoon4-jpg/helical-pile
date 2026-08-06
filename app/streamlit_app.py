"""
Streamlit MVP for the helical pile design calc engine.

Run with:
    streamlit run app/streamlit_app.py

This wraps helical_pile_design 1:1 with the design procedure steps -- it
does not duplicate any calculation logic. If a number here looks wrong,
the bug lives in the library (and should be caught by
tests/test_worked_example_12m.py), not in this file.
"""
import datetime
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")  # see README: p-y solver + many-core OpenBLAS

import streamlit as st
import plotly.graph_objects as go

import cad
import report
from helical_pile_design import loads, geotech, sizing, axial, structural, corrosion, torque, qaqc, connection
from helical_pile_design.lateral_py import (
    ClaySoil, PileSection, solve_py, broms_ultimate_clay_kN, pushover, check_serviceability,
)

st.set_page_config(page_title="Helical pile design -- lighting poles", layout="wide")
st.title("Helical pile design -- lighting pole foundation")
st.caption(
    "Inputs default to the 12 m / medium-stiff-clay worked example. "
    "Every section below maps 1:1 to a numbered step in the design procedure."
)

# =====================================================================
# Sidebar inputs
# =====================================================================
with st.sidebar:
    st.header("Project inputs")

    with st.expander("Project info (calc package cover)", expanded=False):
        project_name = st.text_input("Project name", "")
        project_location = st.text_input("Location / pole ID", "")
        engineer_name = st.text_input("Engineer", "")
        calc_date = st.date_input("Date", datetime.date.today())

    with st.expander("Pole & luminaire (A1-A5)", expanded=True):
        h = st.number_input("Pole height, h (m)", 4.0, 20.0, 12.0, 0.5)
        b_base = st.number_input("Base diameter (m)", 0.10, 0.60, 0.25, 0.01)
        b_top = st.number_input("Top diameter (m)", 0.05, 0.30, 0.10, 0.01)
        A_pole = st.number_input("Pole projected area (m^2)", 0.5, 5.0, 2.10, 0.05)
        W_pole = st.number_input("Pole + arm weight (kN)", 0.2, 5.0, 1.50, 0.05)
        Cd_pole = st.slider("Pole Cd", 0.30, 0.70, 0.50, 0.01)
        epa = st.number_input("Luminaire EPA (m^2)", 0.05, 2.0, 0.50, 0.05)
        W_lum = st.number_input("Luminaire + arm weight (kN)", 0.05, 1.0, 0.25, 0.01)
        arm_ecc = st.number_input("Luminaire arm eccentricity, e_arm (m) -- 0 if twin/centered arm",
                                   0.0, 4.0, 0.0, 0.1)

    with st.expander("Wind (A6-A7)", expanded=True):
        V_ms = st.number_input("Basic wind speed, V (m/s)", 20.0, 90.0, 51.4, 0.1)
        Kz_top = st.number_input("Kz at luminaire height", 0.5, 2.0, 1.04, 0.01)
        Kz_centroid = st.number_input("Kz at pole centroid", 0.5, 2.0, 1.00, 0.01)
        Kd = st.number_input("Kd (directionality)", 0.80, 1.00, 0.95, 0.01)
        G = st.number_input("G (gust factor)", 1.00, 1.30, 1.14, 0.01)
        service_ratio = st.slider("Service/strength pressure ratio", 0.2, 0.7, 0.44, 0.01)
        reveal = st.number_input("Pile reveal above grade (m)", 0.0, 1.0, 0.0, 0.05)

    with st.expander("Soil / geotechnical (A8-A10)", expanded=True):
        su = st.number_input("Su, undrained shear strength (kPa)", 10.0, 200.0, 50.0, 1.0)
        gamma = st.number_input("Total unit weight, gamma (kN/m3)", 14.0, 22.0, 18.5, 0.1)
        gwt = st.number_input("GWT depth (m)", 0.0, 10.0, 3.0, 0.1)
        d_f = st.number_input("Frost depth, d_f (m)", 0.0, 3.0, 1.2, 0.1)
        eps50_manual = st.checkbox("Override eps50 manually", value=False)
        if eps50_manual:
            eps50 = st.number_input("eps50", 0.003, 0.03, 0.007, 0.001)
        else:
            eps50 = geotech.eps50_from_su(su)
            st.caption(f"eps50 = {eps50} (Matlock band, from Su)")
        py_lab_or_cpt = st.checkbox("p-y params from lab/CPT data (not SPT-only)", value=False)

    with st.expander("Trial pile geometry (Step 3)", expanded=True):
        d_shaft_mm = st.selectbox("Shaft OD (mm)", [168, 219, 273, 324], index=2)
        t_nominal_mm = st.number_input("Nominal wall thickness (mm)", 5.0, 20.0, 9.3, 0.1)
        Fy_mpa = st.number_input("Fy (MPa)", 250, 450, 345, 5)
        n_helix = st.selectbox("Number of helices", [2, 3], index=0)
        helix_diam_mm, helix_depth_m = [], []
        cols = st.columns(n_helix)
        for i in range(n_helix):
            with cols[i]:
                helix_diam_mm.append(
                    st.number_input(f"Helix {i+1} dia (mm)", 250, 600, 450, 10, key=f"hd{i}"))
                helix_depth_m.append(
                    st.number_input(f"Helix {i+1} depth (m)", 0.5, 10.0, 3.0 + i * 1.35, 0.05, key=f"hz{i}"))
        standoff = st.number_input("Shaft standoff below bottom helix (m)", 0.0, 1.0, 0.15, 0.05)
        alpha_override = st.slider("Shaft adhesion factor, alpha", 0.4, 1.0, 0.5, 0.01)
        tau_ad = st.number_input("Adfreeze bond stress, tau_ad (kPa)", 0.0, 100.0, 20.0, 1.0)

    with st.expander("Corrosion / design life (Step 7)", expanded=False):
        design_life = st.number_input("Design life (yr)", 25, 100, 75, 5)
        t_zn_um = st.number_input("HDG thickness (um)", 50.0, 150.0, 100.0, 5.0)
        r_zn = st.number_input("Zinc corrosion rate (um/yr)", 1.0, 10.0, 4.0, 0.5)
        r_s = st.number_input("Bare steel corrosion rate (um/yr)", 5.0, 50.0, 20.0, 1.0)
        resistivity = st.number_input("Soil resistivity (ohm-cm)", 200, 20000, 3000, 100)
        ph = st.number_input("Soil pH", 3.0, 10.0, 6.5, 0.1)

    with st.expander("Installation torque (Step 9)", expanded=False):
        Kt = st.number_input("Kt, torque correlation factor (1/m)", 1.0, 40.0, 7.0, 0.5)
        Kt_established = st.checkbox("Kt established by AC358 report", value=False)
        T_rated = st.number_input("Shaft/coupling torque rating (kN*m)", 1.0, 50.0, 15.0, 0.5)

    with st.expander("Pole-to-pile connection (Step 8)", expanded=False):
        n_bolts = st.selectbox("Number of anchor bolts", [4, 6, 8], index=0)
        bolt_circle_r_mm = st.number_input("Bolt circle radius (mm)", 50.0, 400.0, 175.0, 5.0)
        bolt_diam_mm = st.number_input("Bolt diameter, nominal (mm)", 12.0, 50.0, 25.0, 1.0)
        Ab_mm2 = st.number_input("Bolt tensile stress area, Ab (mm^2)", 50.0, 2000.0, 391.0, 1.0)
        Fu_bolt_mpa = st.number_input("Bolt Fu (MPa, e.g. F1554 Gr 55)", 300.0, 900.0, 517.0, 1.0)
        standoff_mm = st.number_input(
            "Leveling-nut standoff (mm) -- bending addend applies above bolt diameter",
            0.0, 150.0, 15.0, 1.0)
        fillet_mm = st.number_input("Shaft-to-plate fillet weld size (mm)", 4.0, 20.0, 8.0, 1.0)
        T_slip_kNm = st.number_input(
            "Pile torsional slip capacity (kN*m) [ASSUMED -- validate]", 0.0, 200.0, 30.0, 1.0)

# =====================================================================
# Run the calc chain (library calls only -- no logic duplicated here)
# =====================================================================
D_SHAFT = d_shaft_mm / 1000.0

with st.status("Running design calculation pipeline...", expanded=False) as status:
    pole = loads.PoleGeometry(height_m=h, base_diam_m=b_base, top_diam_m=b_top,
                               projected_area_m2=A_pole, weight_kN=W_pole, Cd=Cd_pole)
    lum = loads.LuminaireLoad(epa_m2=epa, weight_kN=W_lum, arm_eccentricity_m=arm_ecc)
    wind_strength = loads.WindEnvironment(V_ms=V_ms, Kz_top=Kz_top, Kz_centroid=Kz_centroid,
                                           Kd=Kd, G=G, service_pressure_ratio=service_ratio)
    wind_service = loads.service_wind_environment(wind_strength)

    strength = loads.base_reactions(pole, lum, wind_strength, reveal_m=reveal, dead_load_factor=1.25)
    service = loads.base_reactions(pole, lum, wind_service, reveal_m=reveal)
    st.write(f":material/check_circle: **Step 1 -- Loads:** Vu={strength.V_kN:.1f} kN, "
             f"Mu={strength.M_kNm:.1f} kN·m, Pu={strength.P_kN:.1f} kN")

    helix = sizing.HelixConfig(diameters_m=[d / 1000.0 for d in helix_diam_mm], depths_m=helix_depth_m,
                                shaft_standoff_below_bottom_helix_m=standoff)
    L_pile = helix.tip_depth_m
    embed = sizing.check_embedment(helix, D_SHAFT, d_f, L_pile)
    icon = "check_circle" if embed.all_pass else "error"
    st.write(f":material/{icon}: **Step 3 -- Sizing & embedment:** tip depth {L_pile:.2f} m "
             f"({'OK' if embed.all_pass else 'FAILS'})")

    corr = corrosion.design_corrosion(t_nominal_mm=t_nominal_mm, t_zn_um=t_zn_um, r_zn_um_per_yr=r_zn,
                                       r_s_um_per_yr=r_s, design_life_yr=design_life,
                                       resistivity_ohm_cm=resistivity, ph=ph)
    t_c_mm = corr.t_corroded_mm
    st.write(f":material/check_circle: **Step 7 -- Corrosion:** {t_nominal_mm:.1f} mm nominal -> "
             f"{t_c_mm:.2f} mm corroded over {design_life:.0f} yr")

    L_eff = max(helix.top_depth_m - d_f, 0.0)
    Qu_comp = axial.individual_bearing_compression_kN(helix.diameters_m, D_SHAFT, su, L_eff,
                                                        alpha_override=alpha_override)
    D_h_bottom = helix.diameters_m[helix.depths_m.index(helix.bottom_helix_depth_m)]
    D_h_avg = sum(helix.diameters_m) / len(helix.diameters_m)
    L_c = helix.bottom_helix_depth_m - helix.top_depth_m
    Qu_cyl = axial.cylindrical_shear_compression_kN(
        D_h_bottom_m=D_h_bottom, D_shaft_m=D_SHAFT, su_kpa=su,
        D_h_avg_m=D_h_avg, L_c_m=L_c, L_eff_m=L_eff,
    )
    comp_check = axial.check_compression(Qu_comp, Qu_cyl, strength.P_kN)

    T_frost = axial.frost_uplift_demand_kN(tau_ad, D_SHAFT, d_f)
    Tu = axial.individual_bearing_tension_kN(helix.diameters_m, D_SHAFT, su, L_eff_m=0.0)
    tens_check = axial.check_tension(Tu, Tu * 1.3, T_frost)
    icon = "check_circle" if comp_check.passes and tens_check.passes else "error"
    st.write(f":material/{icon}: **Step 4 -- Axial capacity:** compression FS={comp_check.FS_actual:.1f}, "
             f"tension FS={tens_check.FS_actual:.1f}")

    Fy_kpa = Fy_mpa * 1000.0
    pile_section = PileSection(D_m=D_SHAFT, t_m=t_c_mm / 1000.0)
    soil = ClaySoil(su_kpa=su, gamma_kNm3=gamma, gamma_sub_kNm3=gamma - 9.81, gwt_depth_m=gwt,
                    eps50=eps50, frost_depth_m=d_f)

    Hu = broms_ultimate_clay_kN(su, D_SHAFT, L_m=L_pile, e_m=strength.e_m, d_f_m=d_f)
    sol_service = solve_py(service.V_kN, -service.M_kNm, pile_section, soil, L_m=L_pile)
    sol_strength = solve_py(strength.V_kN, -strength.M_kNm, pile_section, soil, L_m=L_pile)
    svc_check = check_serviceability(sol_service) if sol_service else None
    po = pushover(strength.V_kN, -strength.M_kNm, pile_section, soil, L_m=L_pile)
    lateral_ok = po.passes() and (svc_check.passes if svc_check else False)
    icon = "check_circle" if lateral_ok else "error"
    st.write(f":material/{icon}: **Step 5 -- Lateral p-y solve:** Broms Hu={Hu:.1f} kN, "
             f"pushover lambda_ult={po.lambda_ult:.1f}")

    section = structural.section_properties(D_SHAFT, t_c_mm / 1000.0, Fy_kpa)
    h1 = structural.h1_interaction(strength.P_kN, sol_strength.M_max_kNm if sol_strength else 0.0,
                                    Fy_kpa, section)
    icon = "check_circle" if h1.passes else "error"
    st.write(f":material/{icon}: **Step 6 -- Structural (AISC 360):** H1 ratio={h1.ratio:.3f}")

    P_req = torque.required_ultimate_axial_kN(2.0 * strength.P_kN, 2.0 * T_frost)
    T_min = torque.t_min_kNm(P_req, Kt)
    st.write(f":material/check_circle: **Step 9 -- Installation torque:** "
             f"T_min={T_min:.2f} kN·m at Kt={Kt}")

    bolts = connection.BoltGroup(n_bolts=n_bolts, bolt_circle_radius_m=bolt_circle_r_mm / 1000.0,
                                  Ab_m2=Ab_mm2 / 1e6, Fu_kpa=Fu_bolt_mpa * 1000.0,
                                  bolt_diam_m=bolt_diam_mm / 1000.0)
    bolt_bending_M = connection.bolt_bending_moment_kNm(strength.V_kN, bolts, standoff_mm / 1000.0)
    bolt_res = connection.bolt_check(strength.M_kNm, bolts, bending_moment_kNm=bolt_bending_M)
    weld_res = connection.weld_check(strength.M_kNm, strength.V_kN, D_SHAFT, fillet_mm / 1000.0)
    torsion_ok = connection.torsion_slip_check(T_slip_kNm, strength.Tz_kNm)
    conn_ok = bolt_res.passes and weld_res.passes and torsion_ok
    icon = "check_circle" if conn_ok else "error"
    st.write(f":material/{icon}: **Step 8 -- Pole-to-pile connection:** bolts, weld, and torsion slip "
             f"{'all pass' if conn_ok else 'have failures'}")

    trig_inputs = qaqc.LoadTestTriggerInputs(
        kt_established_by_ac358=Kt_established,
        frost_uplift_relies_on_assumed_values=True,
        py_params_from_lab_or_cpt=py_lab_or_cpt,
        predicted_y_over_limit_ratio=(
            abs(sol_service.y_gl_mm) / 1000.0 / svc_check.y_limit_m if sol_service else 1.0),
        n_production_piles=1,
        variable_or_unfamiliar_soils=False,
    )
    triggers = qaqc.evaluate_load_test_triggers(trig_inputs)
    icon = "check_circle" if not triggers.triggered_tests else "flag"
    trig_summary = "none" if not triggers.triggered_tests else ", ".join(sorted(triggers.triggered_tests))
    st.write(f":material/{icon}: **Step 10 -- QA/QC triggers:** {trig_summary}")

    overall_pass = all([
        embed.all_pass, comp_check.passes, tens_check.passes,
        svc_check.passes if svc_check else False, po.passes(), h1.passes,
        bolt_res.passes, weld_res.passes, torsion_ok,
    ])
    status.update(
        label=("Calculation pipeline complete -- all checks pass" if overall_pass
               else "Calculation pipeline complete -- one or more checks fail"),
        state="complete" if overall_pass else "error",
        expanded=not overall_pass,
    )

# =====================================================================
# Display
# =====================================================================
if overall_pass:
    st.success("Overall: all implemented checks PASS")
else:
    st.error("Overall: one or more checks FAIL -- see detail below")

st.subheader("Step 1 -- Loads")
c1, c2, c3, c4 = st.columns(4)
c1.metric("V_u (kN)", f"{strength.V_kN:.2f}")
c2.metric("M_u (kN*m)", f"{strength.M_kNm:.2f}")
c3.metric("P_u (kN)", f"{strength.P_kN:.2f}")
c4.metric("e = M/V (m)", f"{strength.e_m:.2f}")

st.subheader("Step 2 -- Geotechnical parameterization")
c1, c2 = st.columns(2)
c1.metric("Su, undrained shear strength (kPa)", f"{su:.1f}")
c2.metric("eps50", f"{eps50:.4f}")
if eps50_manual:
    st.caption("eps50 manually overridden -- not derived from the Matlock Su band.")
else:
    su_band = "soft (Su < 25 kPa)" if su < 25.0 else "medium (25 <= Su <= 50 kPa)" if su <= 50.0 else "stiff (Su > 50 kPa)"
    st.caption(f"eps50 = {eps50} from the Matlock Su band -- classified {su_band}.")
st.caption(
    "p-y parameter basis: " + ("lab/CPT data" if py_lab_or_cpt else "SPT correlation only")
    + (" -- triggers a Step 10 load-test recommendation." if not py_lab_or_cpt else ".")
)

st.subheader("Step 3 -- Preliminary sizing / embedment")
st.write(f"Trial shaft {d_shaft_mm} mm OD, pile tip depth {L_pile:.2f} m")
if embed.all_pass:
    st.success(f"Embedment OK (frost req {embed.frost_required_m:.2f} m, "
               f"deep-mode req {embed.deep_mode_required_m:.2f} m)")
else:
    st.warning(f"Embedment FAILS -- frost req {embed.frost_required_m:.2f} m, "
               f"deep-mode req {embed.deep_mode_required_m:.2f} m")
st.caption(embed.lateral_note)

st.subheader("Step 4 -- Axial capacity")
c1, c2 = st.columns(2)
c1.metric("Compression FS", f"{comp_check.FS_actual:.1f}",
          "PASS" if comp_check.passes else "FAIL")
c2.metric("Tension FS (frost uplift)", f"{tens_check.FS_actual:.1f}",
          "PASS" if tens_check.passes else "FAIL")
st.caption(f"Compression governed by {comp_check.governing_method} "
           f"(individual bearing Qu={Qu_comp:.1f} kN, cylindrical shear Qu={Qu_cyl:.1f} kN)")

st.subheader("Step 5 -- Lateral / moment (governing check)")
c1, c2, c3 = st.columns(3)
c1.metric("Broms Hu (kN)", f"{Hu:.1f}", f"FS={Hu/strength.V_kN:.1f}")
c2.metric("Pushover lambda_ult", f"{po.lambda_ult:.1f}", "PASS" if po.passes() else "FAIL")
if svc_check:
    c3.metric("Service y_gl (mm)", f"{sol_service.y_gl_mm:.2f}",
              "PASS" if svc_check.passes else "FAIL")

if sol_service and sol_strength:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sol_service.y_m * 1000, y=-sol_service.z_m,
                              name="Service", mode="lines"))
    fig.add_trace(go.Scatter(x=sol_strength.y_m * 1000, y=-sol_strength.z_m,
                              name="Strength", mode="lines"))
    fig.update_layout(title="Deflected shape", xaxis_title="y (mm)",
                       yaxis_title="depth (m, negative = down)", height=380)
    st.plotly_chart(fig, width='stretch')

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sol_service.M_kNm, y=-sol_service.z_m,
                               name="Service", mode="lines"))
    fig2.add_trace(go.Scatter(x=sol_strength.M_kNm, y=-sol_strength.z_m,
                               name="Strength", mode="lines"))
    fig2.update_layout(title="Bending moment profile", xaxis_title="M (kN*m)",
                        yaxis_title="depth (m)", height=380)
    st.plotly_chart(fig2, width='stretch')

pushover_pts = [(p.lam, p.solution.y_gl_mm) for p in po.points if p.solution]
if pushover_pts:
    lam_arr, y_arr = zip(*pushover_pts)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=y_arr, y=lam_arr, mode="lines+markers"))
    fig3.add_hline(y=2.0, line_dash="dash", annotation_text="FS = 2.0 required")
    fig3.update_layout(title="Pushover curve", xaxis_title="y_gl (mm)",
                        yaxis_title="load multiplier, lambda", height=320)
    st.plotly_chart(fig3, width='stretch')

st.subheader("Step 6 -- Structural (AISC 360, corroded section)")
st.write(f"t_corroded = {t_c_mm:.2f} mm, compact section = {section.compact}")
st.metric("H1 interaction ratio", f"{h1.ratio:.3f}", "PASS" if h1.passes else "FAIL")

st.subheader("Step 7 -- Corrosion")
st.write(f"Zinc life {corr.zinc_life_yr:.0f} yr, sacrificial thickness {corr.t_sac_mm:.2f} mm")
st.caption(corr.classification)

st.subheader("Step 8 -- Pole-to-pile connection")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bolt tension (kN)", f"{bolt_res.T_bolt_kN:.1f}")
c2.metric("Bolt combined stress (MPa)", f"{bolt_res.sigma_total_kpa/1000:.0f}",
          "PASS" if bolt_res.passes else "FAIL")
c3.metric("Weld demand (kN/m)", f"{weld_res.demand_kN_per_m:.1f}", "PASS" if weld_res.passes else "FAIL")
c4.metric("Torsion slip demand (kN*m)", f"{strength.Tz_kNm:.2f}", "PASS" if torsion_ok else "FAIL")
st.caption(
    f"Bolt combined stress = tension {bolt_res.sigma_tension_kpa/1000:.0f} MPa + bending "
    f"{bolt_res.sigma_bending_kpa/1000:.0f} MPa, capacity {bolt_res.sigma_capacity_kpa/1000:.0f} MPa "
    f"({n_bolts} bolts on {bolt_circle_r_mm:.0f} mm radius, {bolt_diam_mm:.0f} mm nominal diameter); "
    f"weld capacity {weld_res.capacity_kN_per_m:.1f} kN/m ({fillet_mm:.0f} mm fillet); "
    f"pile torsional slip capacity {T_slip_kNm:.1f} kN*m required >= 3x Tz "
    f"({3 * strength.Tz_kNm:.2f} kN*m)."
)
if standoff_mm <= bolt_diam_mm:
    st.caption(f"Leveling-nut standoff ({standoff_mm:.0f} mm) does not exceed the bolt diameter "
               f"({bolt_diam_mm:.0f} mm) -- no bending addend per doc Section 8.2.")
else:
    st.caption(f"Bending moment from standoff: M_b = {bolt_bending_M:.3f} kN*m, using a solid-shank "
               f"section modulus from the NOMINAL bolt diameter (overestimates S, so UNDERESTIMATES "
               f"this stress -- replace with the manufacturer's thread-root modulus before final design).")
if strength.Tz_kNm == 0.0:
    st.caption("Tz = 0 (arm eccentricity = 0) -- torsion slip check is trivially satisfied; "
               "set a nonzero luminaire arm eccentricity for single-arm pole configurations.")

st.subheader("Step 9 -- Installation torque")
st.write(f"Required ultimate axial {P_req:.1f} kN, Kt = {Kt} 1/m, T_min = {T_min:.2f} kN*m")
if not Kt_established:
    st.warning("Kt not established by an AC358 report -- treat as assumed until validated (Step 10).")

st.subheader("Step 10 -- QA/QC triggers")
if triggers.triggered_tests:
    st.warning(f"Load tests triggered: {', '.join(sorted(triggers.triggered_tests))}")
    for r in triggers.reasons:
        st.write(f"- {r}")
else:
    st.success("No load test triggers hit")

st.divider()
st.subheader("Calc package export")
st.caption(
    "Generates a Word (.docx) calc package -- cover page, one-page pass/fail checklist, and "
    "Step 1-10 detail with the Step 5 charts embedded -- auto-filled from the current sidebar."
)
if st.button("Generate calc package"):
    ctx = dict(
        project=dict(name=project_name, location=project_location, engineer=engineer_name,
                     date=calc_date.isoformat() if calc_date else ""),
        d_shaft_mm=d_shaft_mm, t_nominal_mm=t_nominal_mm, n_helix=n_helix, L_pile=L_pile,
        strength=strength, service=service,
        embed=embed, comp_check=comp_check, Qu_comp=Qu_comp, Qu_cyl=Qu_cyl,
        tens_check=tens_check, T_frost=T_frost, Tu=Tu,
        Hu=Hu, po=po, sol_service=sol_service, sol_strength=sol_strength, svc_check=svc_check,
        section=section, h1=h1, t_c_mm=t_c_mm, corr=corr,
        bolt_res=bolt_res, weld_res=weld_res, torsion_ok=torsion_ok, bolt_bending_M=bolt_bending_M,
        n_bolts=n_bolts, bolt_circle_r_mm=bolt_circle_r_mm, bolt_diam_mm=bolt_diam_mm,
        standoff_mm=standoff_mm, fillet_mm=fillet_mm, T_slip_kNm=T_slip_kNm,
        P_req=P_req, T_min=T_min, Kt=Kt, Kt_established=Kt_established,
        triggers=triggers, overall_pass=overall_pass,
    )
    docx_bytes = report.build_calc_package_docx(ctx)
    st.download_button(
        "Download calc_package.docx", data=docx_bytes,
        file_name="helical_pile_calc_package.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

st.divider()
st.subheader("Pile configuration CAD drawing")
st.caption(
    "Generates a DXF drawing (elevation + connection plan) of the pile configuration from "
    "the current sidebar inputs -- open in AutoCAD, Civil3D, or any DXF-compatible CAD tool."
)
if st.button("Generate CAD drawing"):
    cad_ctx = dict(
        project_name=project_name, project_location=project_location,
        engineer_name=engineer_name, calc_date=calc_date.isoformat() if calc_date else "",
        d_shaft_mm=d_shaft_mm, t_nominal_mm=t_nominal_mm,
        helix_diam_mm=helix_diam_mm, helix_depth_m=helix_depth_m,
        L_pile_m=L_pile, reveal_m=reveal, d_f_m=d_f,
        n_bolts=n_bolts, bolt_circle_r_mm=bolt_circle_r_mm, bolt_diam_mm=bolt_diam_mm,
    )
    dxf_bytes = cad.build_pile_configuration_dxf(cad_ctx)
    st.download_button(
        "Download pile_configuration.dxf", data=dxf_bytes,
        file_name="pile_configuration.dxf",
        mime="application/dxf",
    )

st.divider()
st.caption(
    "This app wraps helical_pile_design 1:1 with the design procedure steps and duplicates "
    "no calculation logic of its own. Every result here should be independently checked "
    "before use in a stamped submittal."
)
