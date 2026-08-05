"""
Calc-package export -- assembles a Word (.docx) document from the current
session's already-computed results.

Purpose
-------
Pure presentation, same as streamlit_app.py: every number here was already
computed by the library in the app's calc chain before it reaches this
module. This file only formats results into a document -- it duplicates no
calculation logic, exactly like the Streamlit page duplicates none.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

PASS_COLOR = RGBColor(0x2E, 0x7D, 0x4F)
FAIL_COLOR = RGBColor(0xB2, 0x3B, 0x3B)
STRENGTH_COLOR = "#0B72A6"
SERVICE_COLOR = "#A8377E"
WARN_COLOR = "#9C6B1F"


def _status_text(passes: bool) -> str:
    return "PASS" if passes else "FAIL"


def _chart_png_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _deflection_chart(sol_service, sol_strength) -> bytes:
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    if sol_strength:
        ax.plot(sol_strength.y_m * 1000, -sol_strength.z_m, label="Strength", color=STRENGTH_COLOR, linewidth=1.8)
    if sol_service:
        ax.plot(sol_service.y_m * 1000, -sol_service.z_m, label="Service", color=SERVICE_COLOR, linewidth=1.8)
    ax.axvline(0, color="#999999", linewidth=0.8)
    ax.set_xlabel("y (mm)")
    ax.set_ylabel("depth (m, negative = down)")
    ax.set_title("Deflected shape")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(frameon=False)
    return _chart_png_bytes(fig)


def _moment_chart(sol_service, sol_strength) -> bytes:
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    if sol_strength:
        ax.plot(sol_strength.M_kNm, -sol_strength.z_m, label="Strength", color=STRENGTH_COLOR, linewidth=1.8)
    if sol_service:
        ax.plot(sol_service.M_kNm, -sol_service.z_m, label="Service", color=SERVICE_COLOR, linewidth=1.8)
    ax.axvline(0, color="#999999", linewidth=0.8)
    ax.set_xlabel("M (kN·m)")
    ax.set_ylabel("depth (m)")
    ax.set_title("Bending moment profile")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(frameon=False)
    return _chart_png_bytes(fig)


def _pushover_chart(po) -> bytes:
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    pts = [(p.lam, p.solution.y_gl_mm) for p in po.points if p.solution]
    if pts:
        lam_arr, y_arr = zip(*pts)
        ax.plot(y_arr, lam_arr, marker="o", color=STRENGTH_COLOR, linewidth=1.8, markersize=4)
    ax.axhline(2.0, color=WARN_COLOR, linestyle="--", linewidth=1, label="FS = 2.0 required")
    ax.set_xlabel("y_gl (mm)")
    ax.set_ylabel("load multiplier, λ")
    ax.set_title("Pushover curve")
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(frameon=False)
    return _chart_png_bytes(fig)


def _set_base_style(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    for level, size in ((1, 16), (2, 13), (3, 11.5)):
        h = doc.styles[f"Heading {level}"]
        h.font.size = Pt(size)
        h.font.color.rgb = RGBColor(0x16, 0x23, 0x2B)


def _status_row(table, label, value_text, passes) -> None:
    row = table.add_row()
    row.cells[0].text = label
    row.cells[1].text = value_text
    run = row.cells[2].paragraphs[0].add_run(_status_text(passes))
    run.bold = True
    run.font.color.rgb = PASS_COLOR if passes else FAIL_COLOR


def _kv_table(doc, rows) -> None:
    table = doc.add_table(rows=0, cols=2)
    table.style = "Light Grid Accent 1"
    for label, value in rows:
        row = table.add_row()
        row.cells[0].text = str(label)
        row.cells[1].text = str(value)


def _add_picture_row(doc, png_bytes_list, width_in):
    from docx.shared import Inches

    table = doc.add_table(rows=1, cols=len(png_bytes_list))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for cell, png in zip(table.rows[0].cells, png_bytes_list):
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(io.BytesIO(png), width=Inches(width_in))


def build_calc_package_docx(ctx: dict) -> bytes:
    """ctx holds the already-computed result objects from the app's calc
    chain (see app/streamlit_app.py) plus a small `project` dict of
    cover-page metadata. Returns the .docx file as bytes."""
    from docx.shared import Inches

    doc = Document()
    _set_base_style(doc)

    proj = ctx["project"]

    # ---------------- Cover ----------------
    title = doc.add_heading("Helical Pile Foundation Design", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("Lighting Pole Foundation — Calculation Package")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True

    doc.add_paragraph()
    _kv_table(doc, [
        ("Project", proj.get("name") or "—"),
        ("Location / pole ID", proj.get("location") or "—"),
        ("Engineer", proj.get("engineer") or "—"),
        ("Date", proj.get("date") or "—"),
        ("Trial shaft", f"{ctx['d_shaft_mm']:.0f} mm OD × {ctx['t_nominal_mm']:.1f} mm wall, "
                         f"{ctx['n_helix']} helices, tip depth {ctx['L_pile']:.2f} m"),
    ])

    overall = ctx["overall_pass"]
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("OVERALL: " + ("ALL IMPLEMENTED CHECKS PASS" if overall else "ONE OR MORE CHECKS FAIL"))
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = PASS_COLOR if overall else FAIL_COLOR

    disclaimer = doc.add_paragraph(
        "This package is generated directly from the helical_pile_design calculation engine. "
        "Every result should be independently checked by a qualified engineer before use in a "
        "stamped submittal."
    )
    disclaimer.runs[0].italic = True
    disclaimer.runs[0].font.size = Pt(9)

    doc.add_page_break()

    # ---------------- One-page checklist ----------------
    doc.add_heading("Design Check Summary", level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Check", "Result", "Status"
    for cell in hdr:
        cell.paragraphs[0].runs[0].bold = True

    _status_row(table, "Step 3 — Embedment", f"L = {ctx['L_pile']:.2f} m", ctx["embed"].all_pass)
    _status_row(table, "Step 4 — Compression FS", f"{ctx['comp_check'].FS_actual:.1f} (req {ctx['comp_check'].FS_required})", ctx["comp_check"].passes)
    _status_row(table, "Step 4 — Tension FS (frost uplift)", f"{ctx['tens_check'].FS_actual:.1f} (req {ctx['tens_check'].FS_required})", ctx["tens_check"].passes)
    if ctx["svc_check"]:
        _status_row(table, "Step 5 — Service deflection/rotation", f"y_gl={ctx['sol_service'].y_gl_mm:.2f} mm, θ_gl={ctx['sol_service'].theta_gl_deg:.3f}°", ctx["svc_check"].passes)
    _status_row(table, "Step 5 — Pushover λ_ult", f"{ctx['po'].lambda_ult:.1f} (req ≥ 2.0)", ctx["po"].passes())
    _status_row(table, "Step 6 — H1 interaction", f"{ctx['h1'].ratio:.3f} ({ctx['h1'].equation})", ctx["h1"].passes)
    _status_row(table, "Step 8 — Bolt combined stress", f"{ctx['bolt_res'].sigma_total_kpa/1000:.0f} / {ctx['bolt_res'].sigma_capacity_kpa/1000:.0f} MPa", ctx["bolt_res"].passes)
    _status_row(table, "Step 8 — Weld", f"{ctx['weld_res'].demand_kN_per_m:.1f} / {ctx['weld_res'].capacity_kN_per_m:.1f} kN/m", ctx["weld_res"].passes)
    _status_row(table, "Step 8 — Torsion slip", f"Tz={ctx['strength'].Tz_kNm:.2f} kN·m", ctx["torsion_ok"])

    if ctx["triggers"].triggered_tests:
        doc.add_paragraph()
        p = doc.add_paragraph()
        run = p.add_run("Step 10 load tests triggered: " + ", ".join(sorted(ctx["triggers"].triggered_tests)))
        run.bold = True
        run.font.color.rgb = RGBColor(0x9C, 0x6B, 0x1F)

    doc.add_page_break()

    # ---------------- Step 1 ----------------
    doc.add_heading("Step 1 — Loads", level=1)
    s, sv = ctx["strength"], ctx["service"]
    _kv_table(doc, [
        ("V_u (kN)", f"{s.V_kN:.2f}"), ("M_u (kN·m)", f"{s.M_kNm:.2f}"),
        ("P_u (kN)", f"{s.P_kN:.2f}"), ("e = M/V (m)", f"{s.e_m:.2f}"),
        ("V_s (kN)", f"{sv.V_kN:.2f}"), ("M_s (kN·m)", f"{sv.M_kNm:.2f}"),
    ])

    # ---------------- Step 3 ----------------
    doc.add_heading("Step 3 — Preliminary sizing / embedment", level=1)
    embed = ctx["embed"]
    doc.add_paragraph(f"Trial shaft {ctx['d_shaft_mm']:.0f} mm OD, pile tip depth {ctx['L_pile']:.2f} m.")
    _status_paragraph = doc.add_paragraph()
    run = _status_paragraph.add_run(("Embedment OK" if embed.all_pass else "Embedment FAILS") +
                                     f" (frost req {embed.frost_required_m:.2f} m, deep-mode req {embed.deep_mode_required_m:.2f} m)")
    run.bold = True
    run.font.color.rgb = PASS_COLOR if embed.all_pass else FAIL_COLOR
    note = doc.add_paragraph(embed.lateral_note)
    note.runs[0].italic = True
    note.runs[0].font.size = Pt(9)

    # ---------------- Step 4 ----------------
    doc.add_heading("Step 4 — Axial capacity", level=1)
    cc, tc = ctx["comp_check"], ctx["tens_check"]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Check", "FS actual (req)", "Status"
    for cell in hdr:
        cell.paragraphs[0].runs[0].bold = True
    _status_row(table, "Compression", f"{cc.FS_actual:.1f} ({cc.FS_required:.1f})", cc.passes)
    _status_row(table, "Tension (frost uplift)", f"{tc.FS_actual:.1f} ({tc.FS_required:.1f})", tc.passes)
    doc.add_paragraph(
        f"Compression governed by {cc.governing_method} (individual bearing Qu={ctx['Qu_comp']:.1f} kN, "
        f"cylindrical shear Qu={ctx['Qu_cyl']:.1f} kN). Frost uplift demand T_frost={ctx['T_frost']:.1f} kN, "
        f"tension resistance Tu={ctx['Tu']:.1f} kN."
    )

    # ---------------- Step 5 ----------------
    doc.add_heading("Step 5 — Lateral / moment (governing check)", level=1)
    po = ctx["po"]
    sol_service, sol_strength, svc_check = ctx["sol_service"], ctx["sol_strength"], ctx["svc_check"]
    _kv_table(doc, [
        ("Broms Hu (kN)", f"{ctx['Hu']:.1f}  (FS={ctx['Hu']/s.V_kN:.1f})"),
        ("Pushover λ_ult", f"{po.lambda_ult:.1f}  ({'PASS' if po.passes() else 'FAIL'}, req ≥ 2.0)"),
    ])
    if svc_check:
        _kv_table(doc, [
            ("Service y_gl (mm)", f"{sol_service.y_gl_mm:.2f}  (limit {svc_check.y_limit_m*1000:.0f} mm)"),
            ("Service θ_gl (deg)", f"{sol_service.theta_gl_deg:.3f}  (limit {svc_check.theta_limit_deg:.2f}°)"),
        ])
    if sol_strength:
        doc.add_paragraph(f"Strength case: M_max = {sol_strength.M_max_kNm:.1f} kN·m at z = {sol_strength.M_max_depth_m:.2f} m.")

    if sol_service or sol_strength:
        png1 = _deflection_chart(sol_service, sol_strength)
        png2 = _moment_chart(sol_service, sol_strength)
        _add_picture_row(doc, [png1, png2], width_in=3.15)
    png3 = _pushover_chart(po)
    doc.add_picture(io.BytesIO(png3), width=Inches(6.4))

    # ---------------- Step 6 ----------------
    doc.add_heading("Step 6 — Structural (AISC 360, corroded section)", level=1)
    section, h1 = ctx["section"], ctx["h1"]
    _kv_table(doc, [
        ("t_corroded (mm)", f"{ctx['t_c_mm']:.2f}"),
        ("Section compact?", "Yes" if section.compact else "No"),
        ("H1 interaction ratio", f"{h1.ratio:.3f} ({h1.equation})"),
    ])
    p = doc.add_paragraph()
    run = p.add_run(_status_text(h1.passes))
    run.bold = True
    run.font.color.rgb = PASS_COLOR if h1.passes else FAIL_COLOR

    # ---------------- Step 7 ----------------
    doc.add_heading("Step 7 — Corrosion", level=1)
    corr = ctx["corr"]
    _kv_table(doc, [
        ("Zinc life (yr)", f"{corr.zinc_life_yr:.0f}"),
        ("Sacrificial thickness (mm)", f"{corr.t_sac_mm:.2f}"),
        ("Corroded wall (mm)", f"{ctx['t_c_mm']:.2f}"),
    ])
    doc.add_paragraph(corr.classification)

    # ---------------- Step 8 ----------------
    doc.add_heading("Step 8 — Pole-to-pile connection", level=1)
    bolt_res, weld_res = ctx["bolt_res"], ctx["weld_res"]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Check", "Demand / Capacity", "Status"
    for cell in hdr:
        cell.paragraphs[0].runs[0].bold = True
    _status_row(table, "Bolt combined stress (tension + bending)",
                f"{bolt_res.sigma_total_kpa/1000:.0f} / {bolt_res.sigma_capacity_kpa/1000:.0f} MPa", bolt_res.passes)
    _status_row(table, "Weld", f"{weld_res.demand_kN_per_m:.1f} / {weld_res.capacity_kN_per_m:.1f} kN/m", weld_res.passes)
    _status_row(table, "Torsion slip", f"Tz={s.Tz_kNm:.2f} kN·m (3×Tz={3*s.Tz_kNm:.2f})", ctx["torsion_ok"])
    doc.add_paragraph(
        f"{ctx['n_bolts']} bolts on {ctx['bolt_circle_r_mm']:.0f} mm radius, "
        f"{ctx['bolt_diam_mm']:.0f} mm nominal diameter; bolt tension {bolt_res.T_bolt_kN:.1f} kN "
        f"(tension stress {bolt_res.sigma_tension_kpa/1000:.0f} MPa"
        + (f" + bending {bolt_res.sigma_bending_kpa/1000:.0f} MPa from "
           f"{ctx['standoff_mm']:.0f} mm leveling-nut standoff, M_b={ctx['bolt_bending_M']:.3f} kN·m"
           if ctx["standoff_mm"] > ctx["bolt_diam_mm"] else "; no standoff bending addend") +
        f"); {ctx['fillet_mm']:.0f} mm fillet weld; assumed pile torsional slip capacity "
        f"{ctx['T_slip_kNm']:.1f} kN·m [ASSUMED — validate]."
    )

    # ---------------- Step 9 ----------------
    doc.add_heading("Step 9 — Installation torque", level=1)
    _kv_table(doc, [
        ("Required ultimate axial (kN)", f"{ctx['P_req']:.1f}"),
        ("Kt (1/m)", f"{ctx['Kt']}"),
        ("T_min (kN·m)", f"{ctx['T_min']:.2f}"),
        ("Kt established by AC358 report?", "Yes" if ctx["Kt_established"] else "No — assumed"),
    ])

    # ---------------- Step 10 ----------------
    doc.add_heading("Step 10 — QA/QC triggers", level=1)
    triggers = ctx["triggers"]
    if triggers.triggered_tests:
        for reason in triggers.reasons:
            doc.add_paragraph(reason, style="List Bullet")
    else:
        doc.add_paragraph("No load test triggers hit.")

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
