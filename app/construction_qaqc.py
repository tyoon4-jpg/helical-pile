"""
Construction and QA/QC procedure export -- assembles a Word (.docx)
field-executable procedure for installing the pile configuration the
calc chain already sized, using values already computed by the app's
calc chain (Step 3 trial geometry, Step 9 torque, Step 7 corrosion/life,
Step 10 triggers) plus a small set of construction-only inputs collected
separately (owner/AHJ, foundation quantity, obstructions, utility
density) that the structural calc chain has no use for.

Purpose
-------
Pure presentation and narrative procedure text, same spirit as
report.py: numbers here were already computed upstream; this module
only formats them into a document and supplies the surrounding
procedural language. It duplicates no calculation logic.

Governing references assumed by the procedure text below: ICC-ES
AC358, ASTM D1143 (compression), D3689 (tension), D3966 (lateral),
ASTM A123 (galvanizing), AWS D1.1, IBC 2021 Ch. 18, plus the project's
Foundation Design Report. Acceptance values not fixed by one of those
references are labeled "(practice-based default)" and should be
confirmed with the Engineer of Record (EOR) for the specific project;
items with no sensible generic default are left as
"[project-specific -- confirm with EOR]".
"""
from __future__ import annotations

import io

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

HOLD_COLOR = RGBColor(0xB2, 0x3B, 0x3B)
HEAD_COLOR = RGBColor(0x16, 0x23, 0x2B)


# --------------------------------------------------------------------
# Unit helpers -- SI primary, imperial in parentheses
# --------------------------------------------------------------------
def _len_m(v_m: float) -> str:
    return f"{v_m:.2f} m ({v_m * 3.28084:.1f} ft)"


def _dim_mm(v_mm: float) -> str:
    return f"{v_mm:.0f} mm ({v_mm / 25.4:.1f} in)"


def _torque_kNm(v_kNm: float) -> str:
    return f"{v_kNm:.2f} kN·m ({v_kNm * 737.56:,.0f} ft-lb)"


# --------------------------------------------------------------------
# Doc-building helpers (same conventions as report.py)
# --------------------------------------------------------------------
def _set_base_style(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    for level, size in ((1, 16), (2, 13), (3, 11.5)):
        h = doc.styles[f"Heading {level}"]
        h.font.size = Pt(size)
        h.font.color.rgb = HEAD_COLOR


def _h(doc, text, level=1):
    return doc.add_heading(text, level=level)


def _p(doc, text, italic=False, size=None, bold=False, color=None):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.italic = italic
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    return para


def _bullets(doc, items, style="List Bullet"):
    for item in items:
        doc.add_paragraph(item, style=style)


def _hold(doc, text):
    """Mark an explicit hold point: work cannot proceed without EOR sign-off."""
    _p(doc, f"[HOLD — Engineer approval required] {text}", bold=True, color=HOLD_COLOR, size=10.5)


def _kv_table(doc, rows):
    table = doc.add_table(rows=0, cols=2)
    table.style = "Light Grid Accent 1"
    for label, value in rows:
        row = table.add_row()
        row.cells[0].text = str(label)
        row.cells[1].text = str(value)
    return table


def _table(doc, header, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, text in enumerate(header):
        hdr[i].text = text
        hdr[i].paragraphs[0].runs[0].bold = True
    for row_vals in rows:
        row = table.add_row()
        for i, val in enumerate(row_vals):
            row.cells[i].text = str(val)
    return table


# --------------------------------------------------------------------
# Main builder
# --------------------------------------------------------------------
def build_construction_qaqc_docx(ctx: dict) -> bytes:
    """ctx holds already-computed Step 3/7/9/10 results from the app's
    calc chain plus a `construction` dict of inputs the structural calc
    chain doesn't need (owner/AHJ, foundation quantity, obstructions,
    utility density, soil description). Returns the .docx as bytes."""
    doc = Document()
    _set_base_style(doc)
    c = ctx["construction"]
    proj = ctx["project"]

    # ---------------- Cover ----------------
    title = doc.add_heading("Construction and QA/QC Procedure", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("Helical Pile Foundations for Lighting Poles")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True

    doc.add_paragraph()
    _kv_table(doc, [
        ("Project", proj.get("name") or "—"),
        ("Location", proj.get("location") or "—"),
        ("Engineer of Record", proj.get("engineer") or "—"),
        ("Date", proj.get("date") or "—"),
        ("Owner / AHJ", c.get("owner_agency") or "[project-specific — confirm with EOR]"),
        ("AHJ type", c.get("ahj_type") or "[project-specific — confirm with EOR]"),
        ("Quantity of foundations", c.get("n_foundations", "—")),
        ("Pole height", _len_m(ctx["pole_height_m"])),
        ("Pile configuration", ctx["pile_config_text"]),
        ("Minimum installation torque", _torque_kNm(ctx["T_min"])),
        ("Minimum embedment depth", _len_m(ctx["L_pile"])),
        ("Design life", f"{ctx['design_life']:.0f} yr"),
    ])

    disc = doc.add_paragraph(
        "This procedure is generated from the project's helical_pile_design calc chain "
        "(pile configuration, minimum torque, minimum embedment) plus construction inputs "
        "entered separately. It is a field-executable QA/QC procedure, not a substitute for "
        "the Foundation Design Report or the Engineer of Record's project-specific direction. "
        "Every acceptance value either cites its governing standard, is marked as a "
        "practice-based default, or is left as [project-specific — confirm with EOR]."
    )
    disc.runs[0].italic = True
    disc.runs[0].font.size = Pt(9)
    doc.add_page_break()

    _section1(doc, ctx, c)
    _section2(doc)
    _section3(doc, ctx, c)
    _section4(doc, c)
    _section5(doc, ctx)
    _section6(doc)
    _section7(doc, ctx, c)
    _section8(doc, ctx)
    _section9(doc, ctx)
    _section10(doc, ctx, c)
    _section11(doc, ctx)
    _section12(doc, ctx)
    _section13_itp(doc)
    _section14(doc)
    _section15(doc, ctx)
    _section16(doc)
    _final_checklist(doc, ctx, c)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# --------------------------------------------------------------------
# 1. Scope, references, definitions
# --------------------------------------------------------------------
def _section1(doc, ctx, c):
    _h(doc, "1. Scope, References, and Definitions")
    _p(doc, "Scope: this procedure governs construction and quality control for helical pile "
            "foundations supporting lighting poles, from pre-construction submittals through "
            "final acceptance and turnover. It does not cover concrete pier alternatives, "
            "high-mast tower foundations, or the structural design calculation itself (see the "
            "project Foundation Design Report, referenced here as an input, not restated).")

    doc.add_heading("Governing references", level=2)
    _bullets(doc, [
        "ICC-ES AC358 — Acceptance Criteria for Helical Pile Foundation Systems (torque-to-capacity "
        "correlation basis, product certification).",
        "ASTM D1143 — Standard Test Methods for Deep Foundations Under Static Axial Compressive Load.",
        "ASTM D3689 — Standard Test Methods for Deep Foundations Under Static Axial Tensile Load.",
        "ASTM D3966 — Standard Test Methods for Deep Foundations Under Lateral Load.",
        "ASTM A123 — Standard Specification for Zinc (Hot-Dip Galvanized) Coatings on Iron and Steel Products.",
        "AWS D1.1 — Structural Welding Code — Steel.",
        "IBC 2021, Chapter 18 — Soils and Foundations [verify section against the adopted edition].",
        "Project Foundation Design Report — governs pile configuration, minimum torque, and minimum "
        "embedment depth; referenced throughout this procedure, not restated.",
    ])

    doc.add_heading("Definitions", level=2)
    _table(doc, ["Term", "Definition"], [
        ("Ultimate capacity (Qu / Tu)", "The calculated or tested capacity at failure, before any factor of "
                                        "safety is applied. Used for torque-to-capacity correlation (Kt) and "
                                        "load-test acceptance criteria."),
        ("Allowable / design capacity", "Ultimate capacity divided by the project's factor of safety (FS = 2.0 "
                                         "per the Foundation Design Report, Step 4/Step 5). This is the demand "
                                         "the installed pile must be shown to exceed."),
        ("Kt (torque factor)", "Empirical ratio of ultimate axial capacity to final installation torque "
                                "(units 1/length). Governs the field torque-to-capacity correlation; MUST be "
                                "sourced from an AC358 product evaluation report or a site-specific load test, "
                                "never assumed, for any pile this procedure certifies without a load test."),
        ("Termination", "The decision to stop advancing a pile. Requires BOTH minimum installation torque AND "
                         "minimum embedment depth to be satisfied simultaneously — torque alone never "
                         "governs termination (Section 8)."),
        ("Invalid torque reading", "A torque reading taken while advancing through an obstruction, immediately "
                                    "after re-drilling or offsetting, or with visibly fluctuating/chattering "
                                    "drive-head behavior. MUST be flagged in the installation log and excluded "
                                    "from the termination decision (Section 9)."),
    ])

    doc.add_heading("Established project decisions (carried forward, not restated here)", level=2)
    _bullets(doc, [
        "Foundations are moment-dominant: installation defects that reduce lateral/rotational stiffness "
        "(coupling slop, oversized pilot holes, disturbed soil at groundline) are the critical construction "
        "failure modes — not axial bearing.",
        "Soil corrosivity and air-soil interface protection are inspection items under this procedure "
        f"(design life {ctx['design_life']:.0f} yr; see Section 6 and Section 10).",
        f"Soil conditions at this site: {c.get('soil_narrative') or '[project-specific — confirm with EOR]'}.",
    ])


# --------------------------------------------------------------------
# 2. Roles and responsibilities
# --------------------------------------------------------------------
def _section2(doc):
    _h(doc, "2. Roles and Responsibilities")
    _table(doc, ["Role", "Responsibility", "Signs hold point?"], [
        ("Contractor", "Overall means/methods, schedule, submittal compilation, NCR initiation.",
         "No (initiates, does not clear)"),
        ("Installer (certified operator)", "Operates the drive head, logs torque/depth in real time per pile, "
                                            "stops at obstructions and notifies Inspector/Engineer per Section 9.",
         "No"),
        ("Inspector (QC/field)", "Independent witness of installation, verifies torque indicator calibration, "
                                  "completes the per-pile Installation Log, issues NCRs, performs surveillance "
                                  "and witness-point duties per the ITP (Section 13).",
         "Clears W/S points; routes H points to Engineer"),
        ("Engineer of Record (EOR)", "Approves pre-construction submittals, test-pile program, load-test "
                                      "triggers, NCR dispositions, and all explicit [HOLD] points in this "
                                      "procedure.",
         "Yes — all [HOLD] points"),
        ("Owner's Representative", "Contract administration, final acceptance sign-off, turnover package "
                                    "receipt.",
         "Final acceptance only"),
    ])
    _p(doc, "Every hold point marked [HOLD — Engineer approval required] in this procedure requires "
            "the EOR's written approval before work proceeds; the Inspector may witness and document but "
            "cannot itself clear a hold point.", italic=True, size=9.5)


# --------------------------------------------------------------------
# 3. Pre-construction requirements
# --------------------------------------------------------------------
def _section3(doc, ctx, c):
    _h(doc, "3. Pre-Construction Requirements")

    doc.add_heading("Submittals", level=2)
    _table(doc, ["Submittal", "Content", "Reference"], [
        ("Mill certificates", "Chemistry and mechanical properties for shaft and helix plate steel, traceable "
                               "to heat number.", "[verify section] per project spec"),
        ("Galvanizing certificates", "Coating thickness test reports per heat/lot, per ASTM A123 minimum "
                                      "coating-grade table for the governing section thickness.", "ASTM A123"),
        ("Kt basis documentation", "AC358 product evaluation report establishing Kt for the exact shaft/helix "
                                    "product and diameter used, OR a site-specific load test program if no "
                                    "AC358 report covers this product.", "ICC-ES AC358"),
        ("Torque indicator calibration certificate", "Current (≤ 12 months, practice-based default) "
                                                       "calibration traceable to NIST or equivalent, accuracy "
                                                       "±5% of reading or better.", "Section 5"),
        ("Installer qualifications", "Documented experience installing helical piles of comparable diameter/"
                                      "capacity; manufacturer certification where the product requires it.",
         "[project-specific — confirm with EOR]"),
        ("Test pile program (if triggered)", "Scope, location(s), and ASTM standard(s) per Section 12.",
         "ASTM D1143/D3689/D3966"),
    ])

    doc.add_heading("Pre-installation meeting agenda", level=2)
    _bullets(doc, [
        "Review termination criteria and the combined torque-AND-depth rule (Section 8) with the installer crew.",
        "Review obstruction response protocol and offset/pre-drilling limits (Section 9).",
        "Confirm utility locate status and tolerance zones (Section 4).",
        "Confirm torque indicator calibration certificate is current and on site.",
        "Review the per-pile Installation Log (Section 15) and who completes which field.",
        "Confirm load-test program status, if triggered, and reaction setup logistics (Section 12).",
        "Distribute hold-point matrix (Section 2) so the crew knows which decisions require EOR sign-off "
        "before work continues.",
    ])

    _hold(doc, "Submittals above must be reviewed and accepted by the EOR before installation of any "
               "production pile begins.")

    doc.add_heading("Test pile program", level=2)
    _p(doc, "A pre-production test pile program is required when Kt is not already established by an "
            "AC358 report for the exact product/diameter in use, when site soils are variable or "
            "unfamiliar, or per the quantity trigger in Section 12 — one test pile per distinct soil "
            "regime, installed and (if triggered) load tested before production installation begins at "
            "that regime. [project-specific — confirm location(s) and count with EOR].")


# --------------------------------------------------------------------
# 4. Site preparation and utility clearance
# --------------------------------------------------------------------
def _section4(doc, c):
    _h(doc, "4. Site Preparation and Utility Clearance")
    _bullets(doc, [
        "Locate protocol: public one-call locate plus private/designating locate for the owner's known "
        "facilities, minimum [verify section — typically 2 full business days per state one-call rules] "
        "before ground disturbance.",
        "Tolerance zone: hand-expose (potholing) within 0.6 m (2 ft, practice-based default) of any marked "
        "utility before mechanized installation; hand-auger or vacuum-excavate within that zone.",
        "When a locate is inconclusive (unmarked facility suspected, conflicting marks, or abandoned-line "
        "uncertainty): STOP installation at that location, pothole by hand to confirm, and escalate to the "
        "Owner's Representative before resuming — do not proceed on an assumed clearance.",
    ])
    _hold(doc, "Any installation within the tolerance zone of a utility whose status cannot be confirmed "
               "by pothole requires Engineer and Owner's Representative sign-off before proceeding.")
    _p(doc, f"Utility density at this site: {c.get('utility_density') or '[project-specific — confirm with EOR]'}.")
    doc.add_heading("Stop-work triggers", level=2)
    _bullets(doc, [
        "Unmarked or unidentified utility struck or exposed.",
        "Locate marks inconsistent with as-built records by more than 0.3 m (1 ft, practice-based default).",
        "Groundwater, contamination, or unexpected subsurface material inconsistent with the geotechnical "
        "report.",
        "Any condition creating an imminent hazard to crew or the public.",
    ])


# --------------------------------------------------------------------
# 5. Equipment requirements
# --------------------------------------------------------------------
def _section5(doc, ctx):
    _h(doc, "5. Equipment Requirements")
    _kv_table(doc, [
        ("Drive-head torque capacity required", f">= {_torque_kNm(ctx['T_min'])} continuous rating, with "
                                                 f"headroom above the shaft/coupling torque rating "
                                                 f"{_torque_kNm(ctx['T_rated'])} per Step 6/9 of the Foundation "
                                                 f"Design Report — never select a drive head whose rated "
                                                 f"torque is below T_rated."),
        ("Torque measurement method", "Calibrated hydraulic pressure transducer or direct in-line torque "
                                       "sensor — crowd-pressure gauges alone are NOT an acceptable torque "
                                       "measurement method."),
        ("Torque measurement accuracy", "±5% of reading or better (required minimum per this procedure)."),
        ("Calibration frequency", "≤ 12 months (practice-based default), and re-verified at project "
                                   "start-up; calibration records kept on site and included in the turnover "
                                   "package."),
        ("Depth measurement method", "Continuous marked drive-shaft/kelly bar or electronic depth encoder, "
                                      "readable to ±0.05 m (2 in, practice-based default)."),
        ("Verticality/plumb instrumentation", "Digital inclinometer or equivalent mounted to the drive head or "
                                               "mast, readable to 0.1° or better (practice-based default)."),
    ])


# --------------------------------------------------------------------
# 6. Material receiving and inspection
# --------------------------------------------------------------------
def _section6(doc):
    _h(doc, "6. Material Receiving and Inspection")
    _bullets(doc, [
        "Visual inspection on receipt for shipping damage: dented or ovaled shaft sections, bent or cracked "
        "helix plates, damaged coupling threads/pins, coating damage exceeding ASTM A123 repair thresholds.",
        "Coating thickness verification: spot-check per ASTM A123 sampling plan (minimum 10% of pieces or "
        "per the standard's lot-sampling table, whichever governs) using a calibrated magnetic or eddy-"
        "current gauge; record readings.",
        "Storage and handling: store off ground on dunnage, segregate by heat/lot, cap or plug open ends to "
        "exclude debris, do not drag or sling in a way that damages coupling threads or coating.",
        "Rejection criteria: any section with a dimensional deviation outside the manufacturer's tolerance, "
        "coating thickness below the ASTM A123 minimum for that section's governing thickness, a crack in "
        "any weld or base metal, or thread damage that prevents full coupling engagement.",
    ])
    _hold(doc, "Rejected material may not be installed, repaired, or substituted without Engineer review "
               "and written disposition.")


# --------------------------------------------------------------------
# 7. Installation procedure
# --------------------------------------------------------------------
def _section7(doc, ctx, c):
    _h(doc, "7. Installation Procedure")
    _kv_table(doc, [
        ("Pile configuration being installed", ctx["pile_config_text"]),
        ("Minimum embedment depth", _len_m(ctx["L_pile"])),
        ("Minimum installation torque", _torque_kNm(ctx["T_min"])),
    ])
    doc.add_heading("Sequence", level=2)
    _bullets(doc, [
        "1. Layout: stake pile location from the foundation plan/survey control. Plan-location tolerance: "
        "±50 mm (2 in, practice-based default) unless the project spec governs.",
        "2. Pilot alignment: set lead section plumb before engaging soil; an oversized or hand-dug pilot hole "
        "disturbs soil at groundline and reduces lateral/rotational stiffness — pilot hole diameter must "
        "not exceed the shaft OD by more than 25 mm (1 in, practice-based default), and depth must not exceed "
        "the frost/disturbance zone needed for alignment only.",
        "3. Verticality: confirm plumb in two perpendicular directions before advancing; maintain plumbness "
        "within 2% out-of-plumb (≈ 1.15°, practice-based default — verify against the Foundation "
        "Design Report) throughout advance.",
        "4. Crowd pressure and RPM: advance at the equipment manufacturer's recommended crowd-to-torque ratio "
        "for the soil encountered; excessive crowd forces the helix through soil rather than advancing on "
        "its own thread pitch (over-torque without true capacity gain) — [project-specific — confirm "
        "numeric crowd/RPM limits with EOR and equipment manufacturer].",
        "5. Advance rate: target one pitch of travel per revolution (practice-based default, "
        "product-dependent); advance rate significantly exceeding pitch-per-revolution indicates the helix is "
        "cutting rather than screwing into the soil and must be corrected before continuing.",
        "6. Coupling make-up: fully engage and pin/bolt each coupling per the manufacturer's torque spec "
        "before resuming advance; coupling slop is a critical lateral-stiffness defect (Section 1) — "
        "visually and manually verify no play before advancing past each coupling.",
        "7. Torque logging interval: log torque and depth at every full shaft section added, and at minimum "
        "every 0.5 m (≈ 1.6 ft, practice-based default) of advance in the final 3 m (10 ft, practice-based "
        "default) before anticipated termination.",
    ])
    obstructions = c.get("known_obstructions") or "none reported — confirm with geotechnical report"
    _p(doc, f"Site soil conditions: {c.get('soil_narrative') or '[project-specific — confirm with EOR]'}. "
            f"Known obstructions: {obstructions}.", italic=True, size=9.5)


# --------------------------------------------------------------------
# 8. Termination criteria and decision logic
# --------------------------------------------------------------------
def _section8(doc, ctx):
    _h(doc, "8. Termination Criteria and Decision Logic")
    _p(doc, "Termination requires BOTH the minimum installation torque AND the minimum embedment depth to "
            "be satisfied simultaneously. Torque alone is never sufficient — this is the single most "
            "important field rule in this procedure, because the foundation is moment-dominant and depth "
            "governs lateral/rotational stiffness independent of what torque indicates about axial capacity.")
    _kv_table(doc, [
        ("Minimum installation torque, T_min", _torque_kNm(ctx["T_min"])),
        ("Minimum embedment depth, L_min", _len_m(ctx["L_pile"])),
        ("Kt basis", "AC358 product evaluation report" if ctx["Kt_established"]
                     else "ASSUMED — not yet validated by AC358 report or site load test [HOLD until "
                          "resolved per Section 12]"),
    ])
    _table(doc, ["Field condition", "Action"], [
        ("Torque met before minimum depth reached",
         "Continue advancing to minimum depth regardless of torque — depth requirement is never waived "
         "by torque. Log the depth at which torque was first met."),
        ("Minimum depth reached, torque not yet met",
         "Continue advancing past minimum depth until torque is met, up to the shaft/coupling torque rating. "
         "If torque rating is reached before T_min with depth satisfied, STOP and notify the Engineer — "
         "do not exceed the rated torque to force a reading."),
        ("Torque spikes sharply at a discrete depth (suspected obstruction)",
         "Stop advance, do not force through. Flag the reading as invalid and follow the obstruction "
         "protocol in Section 9 before resuming."),
        ("Both criteria met",
         "Terminate. Record final torque, final depth, and total number of invalid/flagged readings "
         "excluded from the termination decision."),
    ])
    _hold(doc, "Reaching the shaft/coupling torque rating before both termination criteria are satisfied "
               "requires Engineer notification and disposition before the pile is accepted or reinstalled.")


# --------------------------------------------------------------------
# 9. Obstruction and refusal management
# --------------------------------------------------------------------
def _section9(doc, ctx):
    _h(doc, "9. Obstruction and Refusal Management")
    _bullets(doc, [
        "Cobble/boulder response: ease crowd pressure, attempt to work through at reduced advance rate for no "
        "more than [project-specific — confirm with EOR, practice-based default: 2-3 attempts / "
        "0.3 m of stalled advance] before treating as refusal.",
        "Offset-and-reinstall: permitted up to 2 attempts within the plan-location tolerance zone "
        "(practice-based default) before escalating to the Engineer for a revised location or foundation "
        "type.",
        "Pre-drilling allowance: pre-drilling through an obstruction is permitted only with Engineer "
        "approval, pilot diameter not exceeding the shaft OD by more than 25 mm (1 in), and stopped before "
        "the anticipated helix bearing zone. Any pre-drilling through or adjacent to the zone where torque "
        "will be read INVALIDATES the Kt correlation for that pile — that pile's torque reading cannot "
        "be used to certify axial capacity and the pile must be flagged for load testing or a documented "
        "engineering disposition.",
        "Notify the Engineer whenever: an obstruction cannot be cleared within the attempt limits above, a "
        "pile is offset more than the plan-location tolerance (Section 10), pre-drilling is needed, or three "
        "or more piles on the same project encounter obstructions at a similar depth (possible systematic "
        "subsurface condition not reflected in the geotechnical report).",
    ])
    _hold(doc, "Any pre-drilling, any offset beyond the plan-location tolerance, and any refusal requiring "
               "relocation or a foundation-type change all require Engineer approval before the pile is "
               "advanced further.")


# --------------------------------------------------------------------
# 10. Tolerances and acceptance criteria
# --------------------------------------------------------------------
def _section10(doc, ctx, c):
    _h(doc, "10. Tolerances and Acceptance Criteria")
    _table(doc, ["Item", "Acceptance criterion", "Basis"], [
        ("Plan location", "±50 mm (2 in) from plan coordinates", "Practice-based default"),
        ("Plumbness", "≤ 2% out-of-plumb (≈ 1.15°)", "Practice-based default — verify "
                                                                    "against Foundation Design Report"),
        ("Top-of-pile / cut-off elevation", "±25 mm (1 in) from plan elevation", "Practice-based default"),
        ("Bolt circle orientation", "±2° from plan orientation about the vertical axis",
         "Practice-based default"),
        ("Minimum embedment depth", _len_m(ctx["L_pile"]) + ", never waived by torque", "Foundation Design "
                                                                                          "Report, Step 3/5"),
        ("Minimum installation torque", _torque_kNm(ctx["T_min"]), "Foundation Design Report, Step 9"),
        ("Cap/adapter fit-up", "Full bearing contact with no gap exceeding 1.5 mm (1/16 in) at any point "
                                "around the circumference", "Practice-based default"),
        ("Coupling engagement", "Full thread/pin engagement per manufacturer spec, zero visible or "
                                 "manually-detectable play", "Manufacturer spec [verify section]"),
    ])


# --------------------------------------------------------------------
# 11. Pole-to-pile connection QC
# --------------------------------------------------------------------
def _section11(doc, ctx):
    _h(doc, "11. Pole-to-Pile Connection QC")
    _kv_table(doc, [
        ("Number of anchor bolts", ctx.get("n_bolts", "[project-specific]")),
        ("Bolt circle radius", _dim_mm(ctx["bolt_circle_r_mm"]) if ctx.get("bolt_circle_r_mm") else
         "[project-specific]"),
        ("Nominal bolt diameter", _dim_mm(ctx["bolt_diam_mm"]) if ctx.get("bolt_diam_mm") else
         "[project-specific]"),
        ("Fillet weld size", _dim_mm(ctx["fillet_mm"]) if ctx.get("fillet_mm") else "[project-specific]"),
        ("Assumed torsional slip capacity", f"{ctx['T_slip_kNm']:.1f} kN·m [ASSUMED — validate "
                                             "against product data]" if ctx.get("T_slip_kNm") else
         "[project-specific]"),
    ])
    _bullets(doc, [
        "Adapter fit: verify full bearing contact between cap plate and pole base plate before torquing "
        "anchor bolts; shim only with manufacturer-approved leveling nuts/shims, never improvised packing.",
        "Anchor bolt / leveling-nut procedure: set leveling nuts to plan elevation first, place pole, then "
        "torque anchor bolts in a star (criss-cross) pattern to the bolt manufacturer's specified torque, in "
        "two passes (snug-tight, then final torque) per AISC/RCSC practice [verify section].",
        "Torque sequence: record each bolt's final torque; re-check the full set after the final bolt in the "
        "sequence to confirm no relaxation.",
        "Field weld inspection per AWS D1.1: 100% visual inspection of all field welds (cap plate-to-shaft, "
        "any structural attachment) for undercut, porosity, crack, and profile per AWS D1.1 Table 6.1 "
        "[verify section]; NDT (e.g., magnetic particle) only where specified by the project spec.",
        "Field touch-up of galvanizing: repair any coating damage from welding, handling, or bolt-up per "
        "ASTM A780 cold-galvanizing compound or metallizing, build to a thickness not less than the ASTM A123 "
        "minimum for the base section — bare steel at the air-soil interface is not an acceptable "
        "condition for turnover.",
    ])
    _hold(doc, "Any field weld exhibiting a crack, or any coating repair exceeding the area/thickness the "
               "project spec allows for field touch-up, requires Engineer disposition before acceptance.")


# --------------------------------------------------------------------
# 12. Load testing program
# --------------------------------------------------------------------
def _section12(doc, ctx):
    _h(doc, "12. Load Testing Program")
    triggers = ctx.get("triggers")
    if triggers and triggers.triggered_tests:
        _p(doc, "Load testing IS triggered for this design as currently configured:", bold=True)
        for reason in triggers.reasons:
            doc.add_paragraph(reason, style="List Bullet")
    else:
        _p(doc, "No Step 10 load-test trigger is currently flagged for this design as configured; the "
                "construction-phase triggers below still apply and may independently require testing.",
            italic=True)

    _table(doc, ["Trigger", "Mode", "ASTM standard"], [
        ("Kt not established by an AC358 report for this exact product", "Axial compression and/or tension",
         "D1143 (compression) / D3689 (tension)"),
        ("Frost-uplift design relies on assumed adfreeze bond stress or sleeve performance", "Axial tension",
         "D3689"),
        ("Lateral serviceability margin < 25%, or p-y parameters not from lab/CPT data", "Lateral",
         "D3966"),
        ("> 50 production piles, or variable/unfamiliar soils across the site", "Axial and/or lateral, one "
         "test pile per soil regime", "D3689 + D3966"),
        ("Construction trigger: torque reading invalidated by pre-drilling/re-drilling at a production pile "
         "relied on for capacity certification", "Per the governing design case for that pile",
         "D1143/D3689/D3966 as applicable"),
    ])

    doc.add_heading("Setup and acceptance", level=2)
    _bullets(doc, [
        "Reaction setup: per the applicable ASTM standard's reaction-pile or dead-load configuration; "
        "reaction piles/anchors must be spaced per the standard's minimum clear distance from the test pile "
        "to avoid interaction [verify section].",
        "Acceptance criterion: measured ultimate (or creep-limited) capacity, divided by the design factor "
        "of safety (2.0 per the Foundation Design Report), must exceed the demand the test pile represents; "
        "net deflection at the design load must not exceed the applicable serviceability limit from the "
        "Foundation Design Report, Step 5.",
        "Witness: Inspector witnesses 100% of load tests; Engineer witnesses or reviews real-time data for "
        "the first test of each soil regime [project-specific — confirm with EOR].",
    ])
    _hold(doc, "Production installation in a soil regime pending a required test-pile result may not proceed "
               "beyond the quantity explicitly pre-approved by the Engineer for that regime.")


# --------------------------------------------------------------------
# 13. Inspection and Test Plan (ITP)
# --------------------------------------------------------------------
def _section13_itp(doc):
    _h(doc, "13. Inspection and Test Plan (ITP)")
    _p(doc, "H = Hold (work stops until cleared), W = Witness (inspector observes in real time), "
            "S = Surveillance (periodic/random check).", italic=True, size=9.5)
    rows = [
        ("Utility locate complete and tolerance zone cleared", "Section 4", "100% of marked utilities "
         "within tolerance zone potholed/confirmed", "Locate tickets, pothole log", "H",
         "Owner's Rep / Contractor"),
        ("Equipment torque indicator calibration verified", "Section 5", "≤ 12 mo calibration, "
         "±5% accuracy", "Calibration certificate", "W", "Inspector"),
        ("Material receiving inspection", "Section 6", "No rejection-criteria defects; coating thickness "
         "≥ ASTM A123 minimum", "Receiving inspection log, coating gauge readings", "S", "Inspector"),
        ("Layout and plan location", "Section 7/10", "±50 mm of plan coordinates", "Survey log", "S",
         "Contractor / Inspector"),
        ("Pilot alignment / plumbness at start of advance", "Section 7/10", "≤ 2% out-of-plumb at start",
         "Installation log", "W", "Inspector"),
        ("Coupling make-up at each joint", "Section 7", "Full engagement, zero visible/manual play",
         "Installation log", "W", "Installer / Inspector"),
        ("Torque and depth logging during advance", "Section 7", "Logged at every section and every 0.5 m "
         "in final 3 m", "Installation log", "W", "Installer"),
        ("Obstruction / refusal event", "Section 9", "Protocol followed, Engineer notified where required",
         "Installation log, NCR if applicable", "H (notify) / W", "Inspector"),
        ("Termination (torque AND depth)", "Section 8/10", "Both criteria met simultaneously, no invalid "
         "readings relied on", "Installation log, inspector sign-off", "H", "Inspector / Engineer"),
        ("Top-of-pile elevation and bolt circle orientation", "Section 10", "±25 mm elevation, ±2° "
         "orientation", "As-built survey", "S", "Inspector"),
        ("Anchor bolt torque sequence", "Section 11", "Manufacturer torque, star pattern, two-pass",
         "Torque wrench log", "W", "Inspector"),
        ("Field weld visual inspection", "Section 11", "AWS D1.1 Table 6.1 acceptance criteria [verify "
         "section]", "Weld inspection report", "H if reject / S otherwise", "Inspector (CWI if required)"),
        ("Galvanizing field touch-up", "Section 11", "Repaired thickness ≥ ASTM A123 minimum",
         "Coating gauge readings", "S", "Inspector"),
        ("Load test (if triggered)", "Section 12", "Per governing ASTM standard's acceptance criterion",
         "Load test report", "H / W", "Engineer / Inspector"),
    ]
    _table(doc, ["Activity", "Reference", "Acceptance criterion", "Verifying document", "H/W/S",
                 "Responsible party"], rows)


# --------------------------------------------------------------------
# 14. Nonconformance and corrective action
# --------------------------------------------------------------------
def _section14(doc):
    _h(doc, "14. Nonconformance and Corrective Action")
    doc.add_heading("NCR trigger list", level=2)
    _bullets(doc, [
        "Termination without both torque AND depth criteria satisfied.",
        "Plumbness, plan-location, elevation, or bolt-circle-orientation tolerance exceeded (Section 10).",
        "Torque reading relied on for certification that was taken through an obstruction or after "
        "re-drilling (Section 1/9).",
        "Coupling installed with detectable play.",
        "Material rejected at receiving and installed anyway.",
        "Field weld defect exceeding AWS D1.1 acceptance criteria.",
        "Galvanizing repair below ASTM A123 minimum thickness.",
        "Load test result below the acceptance criterion in Section 12.",
    ])
    doc.add_heading("Disposition options", level=2)
    _table(doc, ["Disposition", "When applicable"], [
        ("Accept-as-is", "Deviation is within the Engineer's judgment of acceptable margin and documented "
         "with calculation or precedent."),
        ("Repair", "E.g., reweld and re-inspect, re-torque bolts, re-coat damaged galvanizing."),
        ("Replace", "Pile or component cannot be brought into conformance by repair."),
        ("Add pile", "Capacity or stiffness shortfall at one location is resolved by an adjacent "
         "supplemental foundation rather than removing/reinstalling."),
    ])
    _hold(doc, "Every NCR disposition other than a trivial documentation correction requires Engineer "
               "approval before the affected pile is accepted. Re-inspection after corrective action follows "
               "the same ITP line item that originally flagged the nonconformance.")


# --------------------------------------------------------------------
# 15. Documentation and turnover package
# --------------------------------------------------------------------
def _section15(doc, ctx):
    _h(doc, "15. Documentation and Turnover Package")

    doc.add_heading("Per-pile Installation Log template", level=2)
    _p(doc, "Fields only — one row/section per field entry, no sample data.", italic=True, size=9.5)
    _table(doc, ["Field", "Entry"], [
        ("Pile ID", ""),
        ("Date", ""),
        ("Crew", ""),
        ("Equipment (drive head, torque indicator serial no.)", ""),
        ("Target torque / Target depth", f"{_torque_kNm(ctx['T_min'])} / {_len_m(ctx['L_pile'])}"),
        ("Achieved torque (final)", ""),
        ("Achieved depth (final)", ""),
        ("Torque-vs-depth readings (attach log sheet or table)", ""),
        ("Plumbness at termination", ""),
        ("Top-of-pile elevation", ""),
        ("Bolt circle orientation", ""),
        ("Obstructions encountered (depth, description, response taken)", ""),
        ("Invalid/flagged readings (depth, reason)", ""),
        ("NCRs raised (ID, description)", ""),
        ("Inspector sign-off (name, signature, date)", ""),
    ])

    doc.add_heading("Package index", level=2)
    _bullets(doc, [
        "Per-pile Installation Logs (all piles), per the template above.",
        "As-built survey: plan location, top-of-pile elevation, and bolt circle orientation for every pile, "
        "referenced to the same control as the foundation plan.",
        "Photo requirements: pile prior to installation, final termination condition (drive head/torque "
        "readout), coupling make-up, field weld (pre- and post-touch-up), completed connection, minimum 1 per "
        "pile — more where an NCR or obstruction occurred.",
        "Material certifications: mill certs, galvanizing certs, torque indicator calibration certificate.",
        "NCR log with dispositions and Engineer approvals.",
        "Load test report(s), if triggered, with raw data and Engineer's acceptance letter.",
        "Final QA/QC report: executive summary, ITP completion matrix (Section 13) with sign-offs, the "
        "Final Acceptance Checklist (last page of this document) completed and signed.",
    ])


# --------------------------------------------------------------------
# 16. Health and safety interfaces
# --------------------------------------------------------------------
def _section16(doc):
    _h(doc, "16. Health and Safety Interfaces")
    _bullets(doc, [
        "Rotating equipment: establish and enforce an exclusion zone around the drive head and kelly bar "
        "during rotation; no personnel within the zone while torque is being applied.",
        "Overhead lines: maintain OSHA minimum approach distance from energized overhead lines for the mast "
        "height in use before mobilizing equipment to a pole location near overhead conductors "
        "[verify section against the applicable OSHA table for the voltage class present].",
        "Existing lighting circuits: de-energize and verify absence of voltage on any existing circuit before "
        "working within reach of it; coordinate with the owner's electrical utility group per Section 4's "
        "locate/notification protocol.",
        "Excavation-adjacent work: any hand excavation/potholing per Section 4 follows the project's "
        "excavation/competent-person protocol independent of this document.",
    ])


# --------------------------------------------------------------------
# Final acceptance checklist
# --------------------------------------------------------------------
def _final_checklist(doc, ctx, c):
    doc.add_page_break()
    _h(doc, "Final Acceptance Checklist")
    _p(doc, "One page, per project (or per pile group, if the project phases acceptance). All items must "
            "be checked and the Installation Log package complete before Owner's Representative sign-off.",
        italic=True, size=9.5)
    rows = [
        ("All piles terminated on BOTH minimum torque AND minimum embedment depth", "□"),
        ("All invalid/flagged torque readings excluded from certification, or resolved by load test",
         "□"),
        ("Plan location, plumbness, elevation, and bolt circle orientation within tolerance for every pile "
         "(Section 10), or NCR-closed", "□"),
        ("All coupling make-ups verified with zero detectable play", "□"),
        ("Material receiving inspection and coating thickness records complete for all installed material",
         "□"),
        ("Anchor bolt torque sequence complete and logged for every connection", "□"),
        ("Field weld inspection per AWS D1.1 complete, no open weld NCRs", "□"),
        ("Galvanizing field touch-up verified ≥ ASTM A123 minimum thickness, no bare steel at the "
         "air-soil interface", "□"),
        ("All triggered load tests complete and passing (Section 12), or formally waived by the Engineer",
         "□"),
        ("All NCRs closed with Engineer-approved disposition", "□"),
        ("As-built survey complete for all piles", "□"),
        ("Photo documentation complete per Section 15", "□"),
        ("Turnover package assembled and index complete (Section 15)", "□"),
    ]
    _table(doc, ["Item", "Complete"], rows)

    doc.add_paragraph()
    _kv_table(doc, [
        ("Contractor sign-off (name / date)", ""),
        ("Inspector sign-off (name / date)", ""),
        ("Engineer of Record sign-off (name / date)", ""),
        ("Owner's Representative acceptance (name / date)", ""),
    ])
