"""
Site-safety procedure export -- assembles a Word (.docx) field-executable
site-safety procedure for installing the pile configuration and erecting
the pole the calc chain already sized, using values already computed by
the app's calc chain (pole height, pole/luminaire weight) plus
safety-only inputs collected separately (jurisdiction, site type, traffic
exposure, overhead utilities, lifting method, crew size/shift) that the
structural calc chain has no use for.

Purpose
-------
Pure presentation and narrative procedure text, same spirit as
report.py and construction_qaqc.py: numbers here were already computed
upstream; this module only formats them into a document and supplies
the surrounding procedural language. It duplicates no calculation
logic, and does not restate the structural design or construction
QA/QC procedures -- it references them as adjacent documents.

Regulatory basis assumed below is US OSHA 29 CFR 1926 unless the
project's jurisdiction input says otherwise; clause numbers are cited
only where confident and marked [verify clause] elsewhere. Quantitative
values with no fixed regulatory number are labeled "(practice-based
default)"; items with no sensible generic default are left as
"[jurisdiction-specific -- confirm against governing regulation]".
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
def _dist_m(v_m: float) -> str:
    return f"{v_m:.1f} m ({v_m * 3.28084:.0f} ft)"


def _speed_kmh(v_mph: float) -> str:
    return f"{v_mph * 1.60934:.0f} km/h ({v_mph:.0f} mph)"


def _weight_kN(v_kN: float) -> str:
    return f"{v_kN:.2f} kN ({v_kN * 224.809:,.0f} lb)"


# --------------------------------------------------------------------
# Doc-building helpers (same conventions as report.py / construction_qaqc.py)
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
    _p(doc, f"[HOLD — permit required] {text}", bold=True, color=HOLD_COLOR, size=10.5)


def _kv_table(doc, rows):
    table = doc.add_table(rows=0, cols=2)
    table.style = "Light Grid Accent 1"
    for label, value in rows:
        row = table.add_row()
        row.cells[0].text = str(label)
        row.cells[1].text = str(value)
    return table


def _table(doc, header, rows):
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


def _fill_cell_lines(cell, lines):
    cell.paragraphs[0].text = lines[0]
    for extra in lines[1:]:
        cell.add_paragraph(extra)


def _hazard_table(doc, header, rows):
    """rows: list of (hazard_activity, consequence, risk_pre, [control lines], residual, role)."""
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, text in enumerate(header):
        hdr[i].text = text
        hdr[i].paragraphs[0].runs[0].bold = True
    for hazard, consequence, risk_pre, control_lines, residual, role in rows:
        row = table.add_row()
        row.cells[0].text = hazard
        row.cells[1].text = consequence
        row.cells[2].text = risk_pre
        _fill_cell_lines(row.cells[3], control_lines)
        row.cells[4].text = residual
        row.cells[5].text = role
    return table


# --------------------------------------------------------------------
# Main builder
# --------------------------------------------------------------------
def build_site_safety_docx(ctx: dict) -> bytes:
    """ctx holds the pole height/weight already computed by the app's
    calc chain plus a `safety` dict of inputs the structural calc chain
    doesn't need (jurisdiction, site type, traffic exposure, overhead
    utilities, lifting method, crew size/shift). Returns the .docx as
    bytes."""
    doc = Document()
    _set_base_style(doc)
    s = ctx["safety"]
    proj = ctx["project"]

    title = doc.add_heading("Site-Safety Procedure", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph("Helical Pile Installation and Lighting Pole Erection")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.runs[0].italic = True

    doc.add_paragraph()
    _kv_table(doc, [
        ("Project", proj.get("name") or "—"),
        ("Location", proj.get("location") or "—"),
        ("Site Safety Officer", s.get("safety_officer_name") or "[project-specific — confirm]"),
        ("Date", proj.get("date") or "—"),
        ("Jurisdiction / governing regime", s.get("jurisdiction") or "US OSHA 29 CFR 1926 (default — "
         "confirm against the actual project jurisdiction)"),
        ("Site type", s.get("site_type") or "[project-specific — confirm]"),
        ("Posted speed / lane closure", f"{_speed_kmh(s['posted_speed_mph'])}, lane closure "
         f"{'required' if s.get('lane_closure_required') else 'not required'}"
         if s.get("posted_speed_mph") else "[project-specific — confirm]"),
        ("Overhead utilities", s.get("overhead_utility_text") or "none reported — confirm by locate"),
        ("Pole height", _dist_m(ctx["pole_height_m"])),
        ("Pole + luminaire + arm weight (lift planning estimate)",
         _weight_kN(ctx["pole_weight_kN"]) + " — arm/luminaire weight from the structural calc "
         "inputs only; confirm TOTAL erected weight (full pole shaft, base plate, hardware) with the "
         "pole manufacturer before finalizing the lift plan"),
        ("Lifting method", s.get("lifting_method") or "[project-specific — confirm]"),
        ("Crew size / shift", f"{s.get('crew_size', '[project-specific]')} / "
         f"{s.get('shift_hours', '[project-specific]')} hr"
         f"{', night work' if s.get('night_work') else ''}"),
    ])

    disc = doc.add_paragraph(
        "This procedure is a site-safety document, not a substitute for the project's structural "
        "Foundation Design Report or Construction and QA/QC Procedure (referenced here as adjacent "
        "documents, not restated). It does not cover concrete pier alternatives or high-mast tower "
        "erection. Every quantitative control either cites its governing regulation, is labeled a "
        "practice-based default, or is left as [jurisdiction-specific — confirm against governing "
        "regulation]."
    )
    disc.runs[0].italic = True
    disc.runs[0].font.size = Pt(9)
    doc.add_page_break()

    _section1(doc, s)
    _section2(doc)
    _section3(doc)
    _section4(doc)
    _section5_hazard_register(doc)
    _section6_permits(doc)
    _section7_competency(doc)
    _section8_ppe(doc)
    _section9_daily(doc)
    _section10_equipment(doc)
    _section11_emergency(doc)
    _section12_incident(doc)
    _section13_audit(doc)
    _section14_records(doc)
    _final_checklist(doc, ctx, s)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# --------------------------------------------------------------------
# 1. Purpose, scope, governing regulations
# --------------------------------------------------------------------
def _section1(doc, s):
    _h(doc, "1. Purpose, Scope, and Governing Regulations")
    _p(doc, "Purpose: this procedure governs site safety for the installation of helical pile "
            "foundations and the erection of lighting poles, from planning/mobilization through "
            "demobilization. It applies to the entire work sequence: utility locate -> helical pile "
            "installation by hydraulic torque head -> pile cut-off and adapter fit-up -> pole erection "
            "by crane/boom -> luminaire install and electrical termination.")
    _p(doc, "Scope exclusions: this procedure does not restate the structural design procedure or the "
            "Construction and QA/QC Procedure (both referenced as adjacent documents) and does not cover "
            "concrete pier alternatives or high-mast tower erection.")
    doc.add_heading("Governing regulatory basis", level=2)
    jurisdiction_default = ("US OSHA 29 CFR 1926 (default — confirm against the actual project "
                             "jurisdiction, e.g. Korea KOSHA Occupational Safety and Health Act / Serious "
                             "Accidents Punishment Act, or other)")
    _bullets(doc, [
        f"Jurisdiction for this project: {s.get('jurisdiction') or jurisdiction_default}.",
        "29 CFR 1926 Subpart CC — Cranes and Derricks in Construction [verify clause against current "
        "edition].",
        "29 CFR 1926 Subpart K — Electrical.",
        "29 CFR 1926 Subpart M — Fall Protection.",
        "29 CFR 1926 Subpart V — Power Transmission and Distribution (minimum approach distances).",
        "NFPA 70E — Standard for Electrical Safety in the Workplace (arc-flash boundaries, qualified-"
        "worker requirements).",
        "MUTCD (Manual on Uniform Traffic Control Devices), or the jurisdiction's equivalent, for temporary "
        "traffic control.",
        "This procedure's quantitative controls default to US practice where the project jurisdiction is "
        "not US OSHA; re-verify every numeric value against the actual governing regulation before use.",
    ])
    _p(doc, "Key project decision carried forward: a helical pile foundation removes some hazards "
            "present on a concrete pier foundation (confined space, mass-excavation collapse, because "
            "there is minimal spoil) but this MUST NOT be used to justify relaxing controls for the "
            "hazards that remain or are introduced by this method — rotating torque equipment, "
            "utility strikes (a rotating pile can strike an unlocated utility even with no open "
            "excavation), crane/lifting operations, live traffic exposure, and energized circuits.",
        bold=True)


# --------------------------------------------------------------------
# 2. Roles, responsibilities, authority
# --------------------------------------------------------------------
def _section2(doc):
    _h(doc, "2. Roles, Responsibilities, and Authority")
    _table(doc, ["Role", "Responsibility", "May stop work?"], [
        ("Site Safety Officer", "Overall site safety authority; approves JHAs, permits, and hold points; "
         "leads tailgate briefings; investigates incidents.", "Yes — unconditional"),
        ("Competent/Qualified Person (per task)", "Designated per 29 CFR 1926 definitions for the "
         "specific hazard (e.g., utility locate, rigging); authorized to make on-the-spot hazard "
         "determinations.", "Yes — for their designated hazard"),
        ("Crane Operator", "Operates lifting equipment within the load chart and lift plan; refuses any "
         "lift outside rated capacity or safe wind/ground conditions.", "Yes"),
        ("Signal Person", "Qualified per 29 CFR 1926.1428; directs crane movements when the operator's "
         "view is obstructed.", "Yes"),
        ("Rigger", "Qualified per 29 CFR 1926.1401; selects and inspects rigging, confirms load weight "
         "and center of gravity.", "Yes"),
        ("Qualified Electrical Worker", "Authorized to work on or near energized lighting circuits per "
         "NFPA 70E; performs lockout/tagout and test-before-touch.", "Yes"),
        ("Flagger", "Controls traffic through the work zone per the temporary traffic control plan.",
         "Yes — for traffic-related hazards"),
        ("Spotter", "Dedicated observer for overhead-line clearance, swing radius, or blind-spot "
         "operations; maintains continuous communication with the equipment operator.", "Yes"),
        ("Every worker on site", "Any worker who identifies an unsafe condition.", "Yes — see "
         "Section 3"),
    ])


# --------------------------------------------------------------------
# 3. Stop-work authority
# --------------------------------------------------------------------
def _section3(doc):
    _h(doc, "3. Stop-Work Authority")
    _p(doc, "Every worker on this site — regardless of role, employer, or seniority — holds "
            "stop-work authority. Any worker who identifies a condition they believe is unsafe stops the "
            "affected work immediately, notifies the Site Safety Officer (or the most senior person "
            "present if the Site Safety Officer is unavailable), and work does not resume until the "
            "condition is resolved or a competent/qualified person determines it is safe to proceed. No "
            "reprisal, formal or informal, applies to a stop-work action exercised in good faith.", bold=True)
    doc.add_heading("Non-negotiable stop triggers (not an exhaustive list)", level=2)
    _bullets(doc, [
        "Any part of equipment, a raised pole, or a load approaches within the minimum approach distance "
        "of an energized overhead line (Section 5) without an approved permit in place.",
        "A utility locate is inconclusive, missing, or conflicts with observed conditions (Section 5) — "
        "mechanized advance stops regardless of schedule pressure.",
        "Sustained wind exceeds the lift's wind speed limit (Section 5) during any suspended-load operation.",
        "Any rigging, sling, or lifting hardware shows damage, deformation, or exceeds its inspection "
        "interval (Section 10).",
        "A worker is inside the rotating torque head's exclusion radius, a crane's exclusion zone, or "
        "under a suspended load.",
        "Lightning is observed or thunder is heard within the stand-down distance (Section 5).",
        "Any energized-circuit work proceeds without a verified zero-energy state or an approved "
        "energized-work permit (Section 6).",
    ])


# --------------------------------------------------------------------
# 4. Risk assessment framework
# --------------------------------------------------------------------
def _section4(doc):
    _h(doc, "4. Risk Assessment Framework")
    _p(doc, "A Job Hazard Analysis (JHA) is required for every distinct task in the work sequence "
            "(utility locate, pile installation, cut-off/fit-up, crane lift/pole erection, luminaire "
            "install/electrical termination) before that task begins on site, and is reviewed/re-issued "
            "whenever the task, crew, equipment, or site conditions change materially.")
    doc.add_heading("Risk matrix (likelihood x severity)", level=2)
    _table(doc, ["Likelihood \\ Severity", "Minor (first aid)", "Moderate (medical treatment / "
                 "lost time)", "Major (hospitalization / permanent injury)", "Catastrophic "
                 "(fatality)"], [
        ("Rare", "Low", "Low", "Medium", "High"),
        ("Possible", "Low", "Medium", "High", "Extreme"),
        ("Likely", "Medium", "High", "Extreme", "Extreme"),
        ("Frequent/continuous exposure", "Medium", "High", "Extreme", "Extreme"),
    ])
    _p(doc, "Residual-risk acceptance threshold: work may proceed only once controls bring the residual "
            "rating to Low or Medium (practice-based default — confirm against the project's or "
            "jurisdiction's risk-acceptance policy). A residual rating of High or Extreme requires "
            "additional controls before work proceeds and is not accepted by schedule pressure alone.")
    _p(doc, "Approval: the Site Safety Officer approves every JHA and residual-risk determination before "
            "the associated task begins; a High or Extreme residual rating additionally requires the "
            "Competent/Qualified Person for that hazard to concur in writing.")


# --------------------------------------------------------------------
# 5. Hazard register
# --------------------------------------------------------------------
def _section5_hazard_register(doc):
    _h(doc, "5. Hazard Register and Controls by Hierarchy")
    _p(doc, "Controls below follow the hierarchy of controls — eliminate, substitute, engineer, "
            "administrative, PPE — in that order of preference; PPE is the last line of defense, "
            "never the primary control. \"Not practicable\" is stated explicitly where a higher-order "
            "control does not apply to a given hazard, rather than left blank.", italic=True, size=9.5)
    _p(doc, "Minimal excavation does NOT remove the underground-utility-strike hazard: a rotating "
            "helical pile can strike an unlocated or mismarked utility exactly as a mechanized auger or "
            "excavator can — this hazard is carried in the register below at the same severity as on "
            "a conventional deep-foundation site.", bold=True)

    header = ["Hazard / Activity", "Consequence", "Risk (pre-control)", "Controls by hierarchy",
              "Residual risk", "Responsible role"]
    rows = [
        ("Rotating torque head and drive shaft — entanglement, torque-reaction-arm strike, pinch "
         "points", "Entanglement, crush/pinch injury, struck-by reaction-arm swing", "High", [
            "Eliminate: not practicable — rotation is required to install the pile.",
            "Substitute: n/a.",
            "Engineer: drive-head guarding per OEM; torque-reaction arm restrained/anchored; proximity "
            "interlock where equipped.",
            "Administrative: enforced exclusion radius = 3.0 m (10 ft) around the mast while rotating "
            "(practice-based default — confirm against OEM swing radius + reaction-arm length); no "
            "coupling work until rotation has fully stopped and is locked out.",
            "PPE: no loose clothing, jewelry, or unrestrained long hair near rotating components; "
            "task-rated gloves.",
        ], "Low", "Installer / Competent Person"),

        ("Underground utility strike", "Electrocution, explosion/fire (gas), asphyxiation, service "
         "outage", "High", [
            "Eliminate: relocate the pile away from a confirmed conflict per the Engineer of Record "
            "(see Construction and QA/QC Procedure, Section 4).",
            "Substitute: hand excavation or vacuum excavation within the utility tolerance zone instead "
            "of mechanized advance.",
            "Engineer: n/a.",
            "Administrative: locate protocol per the one-call rules for this jurisdiction (practice-based "
            "default: minimum 2 full business days before ground disturbance); hand-expose within 0.6 m "
            "(2 ft) of any marked utility before mechanized advance; STOP if the locate is inconclusive "
            "and escalate per Section 3.",
            "PPE: n/a.",
            "NOTE: this hazard is never fully eliminated by the helical method — minimal excavation "
            "does not protect against an UNLOCATED utility struck by the rotating pile.",
        ], "Medium (cannot be reduced to Low by this method alone)", "Site Safety Officer / Competent "
         "Person"),

        ("Overhead power line contact", "Electrocution, arc flash/blast, fire", "Extreme", [
            "Eliminate: route equipment travel and pole-erection positions clear of all overhead lines "
            "where the site layout allows.",
            "Substitute: n/a.",
            "Engineer: insulating line hose/blankets or temporary line relocation where the utility owner "
            "agrees; insulated link on the load line where applicable.",
            "Administrative: minimum approach distance (MAD) by voltage class, per 29 CFR 1926.1408 "
            "Table A for crane/lift operations — up to 50 kV: 3.05 m (10 ft); >50-200 kV: 4.6 m "
            "(15 ft); >200-350 kV: 6.1 m (20 ft); >350-500 kV: 7.6 m (25 ft); >500-750 kV: 10.7 m (35 ft); "
            ">750-1000 kV: 13.7 m (45 ft) [verify clause against current 1926.1408 edition and against the "
            "jurisdiction's governing regulation if not US OSHA]. Dedicated spotter whenever equipment can "
            "approach within the MAD; request de-energization or insulated barriers from the utility owner "
            "when the MAD cannot otherwise be maintained.",
            "PPE: n/a — PPE does not protect against overhead-line contact; distance and "
            "de-energization are the controls.",
        ], "Medium", "Equipment Operator / Spotter / Site Safety Officer"),

        ("Mobile equipment and swing radius", "Struck-by, crush injury, pedestrian/worker contact", "High",
         [
            "Eliminate: n/a.",
            "Substitute: n/a.",
            "Engineer: back-up alarms, cameras/mirrors on all mobile equipment.",
            "Administrative: barricaded/marked travel routes; ground-level spotter required for any "
            "backing or swing movement where the operator's view is obstructed; no personnel in blind-spot "
            "zones; pre-task briefing on travel routes for the shift.",
            "PPE: high-visibility apparel (Section 8) for anyone on foot in the work area.",
        ], "Low", "Equipment Operator / Spotter"),

        ("Crane and lifting operations for pole erection", "Struck-by dropped/swinging load, crane "
         "tip-over, rigging failure", "Extreme", [
            "Eliminate: n/a — lifting is required to erect the pole.",
            "Substitute: n/a.",
            "Engineer: rated rigging selected for the actual load weight and configuration; tagline "
            "control on every suspended load.",
            "Administrative: written lift plan required for every lift (critical-lift plan required when "
            "the lift exceeds 75% of rated capacity, uses multiple cranes, or is otherwise non-standard "
            "[jurisdiction-specific — confirm threshold] — [HOLD — permit required], see "
            "Section 6); load chart and rated capacity verified for the actual radius/configuration before "
            "each lift; rigging inspected before each shift and before each lift by a qualified rigger "
            "(Section 10); exclusion zone during any lift = the greater of (boom length + 3 m) or (lift "
            "radius + 3 m) (practice-based default), barricaded, no personnel under a suspended load at "
            "any time; wind speed limit = cease lifting at sustained wind exceeding 32 km/h (20 mph) or "
            "this crane's load-chart limit, whichever is lower (practice-based default — confirm "
            "against this crane's load chart).",
            "PPE: hard hat, high-visibility apparel for all personnel in the lift area.",
        ], "Medium", "Crane Operator / Rigger / Signal Person / Site Safety Officer"),

        ("Live traffic exposure", "Worker struck by vehicle, vehicle intrusion into work zone", "High", [
            "Eliminate: schedule off-peak or night work where permitted and where night-work lighting "
            "controls (below) are in place.",
            "Substitute: n/a.",
            "Engineer: temporary traffic control devices — cones, barrels, barriers, arrow boards, "
            "portable lighting for night work.",
            "Administrative: temporary traffic control (TTC) plan per MUTCD or the jurisdiction's "
            "equivalent [verify clause]; taper and buffer length per the posted-speed formula in MUTCD "
            "Table 6C-3 [verify clause — compute from this project's actual posted speed]; certified "
            "flagger required for any lane closure; minimum 2 flaggers for a two-way single-lane closure.",
            "PPE: ANSI/ISEA 107 Class 2 high-visibility apparel minimum for anyone exposed to traffic; "
            "Class 3 required for posted speeds exceeding 72 km/h (45 mph) or for any night work "
            "(regulatory per ANSI/ISEA 107 and MUTCD guidance — best practice to apply Class 3 by "
            "default on any active roadway site).",
        ], "Medium", "Flagger / TTC Supervisor / Site Safety Officer"),

        ("Energized lighting circuits", "Electrocution, arc flash/blast, burns", "Extreme", [
            "Eliminate: de-energize and lock out before any termination, splicing, or troubleshooting "
            "work.",
            "Substitute: n/a.",
            "Engineer: lockable disconnects; arc-flash labeling at the panel/circuit.",
            "Administrative: test-before-touch with a calibrated meter on every conductor before contact, "
            "every time, even after lockout/tagout is applied; qualified-electrical-worker-only for any "
            "task on or near an energized or potentially energized circuit; arc-flash boundary per NFPA "
            "70E Table 130.4(D)(a) for this circuit's voltage and incident-energy category [jurisdiction/"
            "voltage-specific — confirm against this circuit's arc-flash study]; energized work "
            "requires an approved energized-electrical-work permit (Section 6) — [HOLD — permit "
            "required].",
            "PPE: voltage-rated insulating gloves with leather protectors, arc-rated clothing sized to the "
            "incident-energy category, face shield/balaclava where the arc-flash study requires it.",
        ], "Low after LOTO / Medium if energized work is unavoidable", "Qualified Electrical Worker"),

        ("Manual handling and sharp edges", "Strain/sprain injury, laceration", "Medium", [
            "Eliminate: n/a.",
            "Substitute: n/a.",
            "Engineer: mechanical lifting aid (crane, chain hoist, or equivalent) required for any pile "
            "section or helix plate above 23 kg (51 lb) (practice-based default per the NIOSH lifting "
            "equation).",
            "Administrative: two-person lift below the mechanical-aid threshold where the load remains "
            "awkward; edge guards/covers on helix plates during handling and storage.",
            "PPE: cut-resistant gloves, ANSI/ISEA 105 cut level A3 minimum (practice-based default).",
        ], "Low", "Installer crew"),

        ("Hot work and fume exposure (field welding, galvanizing touch-up)", "Fire, burns, metal fume "
         "fever, respiratory injury", "Medium", [
            "Eliminate: shop-apply coatings/welds where practicable instead of field work.",
            "Substitute: cold-galvanizing compound in place of open-flame metallizing where the repair "
            "area/thickness allows.",
            "Engineer: local exhaust ventilation for galvanizing touch-up fume.",
            "Administrative: hot work permit required for all field welding (Section 6) — [HOLD "
            "— permit required]; fire watch maintained for a minimum 30 minutes after welding stops "
            "(practice-based default per NFPA 51B [verify clause]); fire extinguisher staged at the work "
            "location; crew briefed on metal fume fever symptoms (flu-like onset hours after exposure) and "
            "told to report them.",
            "PPE: welding-rated respirator or supplied air where ventilation is insufficient per exposure "
            "assessment; hearing protection for associated grinding — noise exposure limit 90 dBA "
            "8-hour TWA, action level 85 dBA (29 CFR 1926.52, regulatory).",
        ], "Medium", "Welder / Site Safety Officer"),

        ("Aerial lift / work at height for luminaire install", "Fall, struck-by falling tool/material",
         "High", [
            "Eliminate: no-climb-the-pole rule — free climbing the pole is prohibited; aerial lift "
            "or bucket truck only.",
            "Substitute: n/a.",
            "Engineer: fall arrest anchored to a manufacturer-rated anchor point on the lift platform.",
            "Administrative: rescue plan on file and briefed before work begins; daily lift inspection "
            "(Section 10); tools tethered to prevent dropped-object strikes.",
            "PPE: full-body harness with shock-absorbing lanyard, rated per ANSI Z359.1 [verify clause]; "
            "hard hat with chin strap.",
        ], "Low", "Lift Operator / Qualified Electrical Worker"),

        ("Noise, vibration, and environmental exposure", "Hearing loss, hand-arm vibration syndrome "
         "(HAVS), heat/cold stress injury, lightning strike", "Medium", [
            "Eliminate: n/a.",
            "Substitute: lower-vibration tool selection where available for repetitive tasks.",
            "Engineer: anti-vibration tool handles/gloves where applicable.",
            "Administrative: noise exposure limit 90 dBA 8-hour TWA, action level 85 dBA (29 CFR 1926.52, "
            "regulatory); HAVS exposure action value 2.5 m/s² A(8), limit value 5.0 m/s² A(8) "
            "(best-practice reference, EU Directive 2002/44/EC / ACGIH TLV — OSHA has no fixed "
            "numeric PEL for vibration [jurisdiction-specific]); heat-stress work/rest cycle per NIOSH "
            "WBGT-based tables [jurisdiction-specific — some jurisdictions set a fixed threshold, "
            "e.g. Cal/OSHA]; lightning/severe-weather stand-down per the 30-30 rule (practice-based "
            "default): suspend outdoor work when lightning is observed or thunder heard within 10 km "
            "(6 mi), resume no sooner than 30 minutes after the last strike/thunder.",
            "PPE: hearing protection rated to the exposure, weather-appropriate clothing.",
        ], "Medium", "Site Safety Officer"),
    ]
    _hazard_table(doc, header, rows)


# --------------------------------------------------------------------
# 6. Permit and hold-point register
# --------------------------------------------------------------------
def _section6_permits(doc):
    _h(doc, "6. Permit and Hold-Point Register")
    _table(doc, ["Activity", "Trigger condition", "Approver"], [
        ("Hand-exposure / excavation within the utility tolerance zone when a locate is inconclusive",
         "[HOLD — permit required] Locate marks missing, conflicting, or inconsistent with observed "
         "conditions", "Site Safety Officer + Utility Owner"),
        ("Crane critical lift", "[HOLD — permit required] Lift exceeds 75% of rated capacity, uses "
         "multiple cranes, or is otherwise non-standard [jurisdiction-specific — confirm threshold]",
         "Site Safety Officer + Crane Operator/Qualified Person"),
        ("Work within the minimum approach distance of an energized overhead line", "[HOLD — permit "
         "required] Equipment, load, or raised pole cannot clear the MAD in Section 5", "Site Safety "
         "Officer + Utility Owner (de-energization request)"),
        ("Hot work (field welding, grinding near combustibles)", "[HOLD — permit required] Any open "
         "flame, arc, or spark-producing operation", "Site Safety Officer"),
        ("Energized electrical work", "[HOLD — permit required] De-energization/LOTO is not "
         "achievable for the task", "Qualified Electrical Worker + Site Safety Officer"),
        ("Night work", "[HOLD — plan required] Any shift extending into hours of darkness",
         "Site Safety Officer (lighting plan approved)"),
        ("Lane closure / traffic control activation", "[HOLD — permit required] Any work requiring "
         "a TTC plan to be put into effect", "TTC Supervisor / jurisdiction traffic authority"),
    ])


# --------------------------------------------------------------------
# 7. Competency, training, authorization
# --------------------------------------------------------------------
def _section7_competency(doc):
    _h(doc, "7. Competency, Training, and Authorization")
    _table(doc, ["Role", "Required certification / training"], [
        ("Site Safety Officer", "OSHA 30-hour Construction (or jurisdiction equivalent) [verify], plus "
         "site-specific orientation to this procedure."),
        ("Competent/Qualified Person (per hazard)", "Meets the 29 CFR 1926 definition for the specific "
         "hazard assigned (e.g., excavation/utility, rigging) [verify clause for the jurisdiction in "
         "use]."),
        ("Crane Operator", "Certified per 29 CFR 1926.1427 (e.g., NCCCO or accredited equivalent)."),
        ("Signal Person", "Qualified per 29 CFR 1926.1428."),
        ("Rigger", "Qualified per 29 CFR 1926.1401."),
        ("Qualified Electrical Worker", "Meets the qualified-person definition of 29 CFR 1926 Subpart K "
         "and NFPA 70E."),
        ("Flagger", "Certified per the jurisdiction's DOT flagger training program [verify]."),
    ])
    _p(doc, "Verification: the Site Safety Officer verifies and retains current certification records for "
            "every role above before that person performs the associated task (Section 14).")
    _p(doc, "Visitor and new-hire orientation: every new crew member and every visitor entering an active "
            "work zone receives a site-specific hazard briefing before entry, logged by name, date, and "
            "briefing content.")


# --------------------------------------------------------------------
# 8. PPE matrix
# --------------------------------------------------------------------
def _section8_ppe(doc):
    _h(doc, "8. PPE Matrix")
    _table(doc, ["Task", "Required PPE", "Standard"], [
        ("General site presence (any active work area)", "Hard hat; safety glasses; high-visibility "
         "vest/shirt (Class 2 minimum); steel-toe boots", "ANSI Z89.1 / ANSI Z87.1 / ANSI-ISEA 107 / "
         "ASTM F2413"),
        ("Roadway-adjacent or night work", "Upgrade to high-visibility apparel Class 3", "ANSI/ISEA 107 "
         "(best practice to default to Class 3 on any active roadway site)"),
        ("Torque head operation, sustained noise >85 dBA", "Hearing protection rated to the measured "
         "exposure, in addition to general PPE", "29 CFR 1926.52 (action level)"),
        ("Rigging / signaling", "Task-rated gloves, in addition to general PPE", "ANSI/ISEA 105 (select "
         "cut level per task)"),
        ("Energized electrical work (permit-approved only)", "Voltage-rated insulating gloves with "
         "leather protectors; arc-rated clothing sized to the incident-energy category; face shield/"
         "balaclava per the arc-flash study — general PPE is INSUFFICIENT for this task", "NFPA 70E "
         "/ ASTM D120 / ASTM F696 — upgraded protection mandatory, not optional"),
        ("Hot work / field welding", "Welding helmet, FR clothing, welding gloves — general PPE is "
         "insufficient", "ANSI Z87.1 (welding filter) — upgraded protection mandatory"),
        ("Galvanizing touch-up (zinc fume)", "NIOSH-approved, fit-tested respirator per exposure "
         "assessment; chemical-splash goggles", "NIOSH 42 CFR 84 [verify clause]"),
        ("Aerial lift / work at height", "Full-body harness with shock-absorbing lanyard; hard hat with "
         "chin strap", "ANSI Z359.1 [verify clause]"),
    ])


# --------------------------------------------------------------------
# 9. Daily routine
# --------------------------------------------------------------------
def _section9_daily(doc):
    _h(doc, "9. Daily Routine")
    doc.add_heading("Pre-shift equipment inspection checklist (summary -- full checklist per Section 10)",
                     level=2)
    _bullets(doc, [
        "Torque head: guarding intact, no hydraulic leaks, reaction arm undamaged and secured.",
        "Hoses and hydraulics: no visible bulge, abrasion, or leak.",
        "Rigging and slings: no deformation, crack, or wear exceeding the manufacturer's limit.",
        "Crane: pre-operational inspection per 29 CFR 1926.1412 [verify clause] complete and logged.",
        "Aerial lift: pre-operational inspection per the manufacturer's checklist complete and logged.",
    ])
    doc.add_heading("Tailgate / pre-task briefing", level=2)
    _p(doc, "Held before every shift and whenever the task, crew, equipment, or conditions change. "
            "Template below (fields only, no sample data).")
    _table(doc, ["Field", "Entry"], [
        ("Date / time", ""),
        ("Task(s) covered", ""),
        ("Crew members present (names)", ""),
        ("Weather / wind conditions", ""),
        ("Hazards reviewed (from JHA/hazard register)", ""),
        ("Controls confirmed in place", ""),
        ("Permits/hold points active today", ""),
        ("Emergency muster point reviewed", ""),
        ("Worker questions/concerns raised", ""),
        ("Briefing leader sign-off (name, signature)", ""),
    ])
    doc.add_heading("End-of-shift site securing", level=2)
    _bullets(doc, [
        "Cap or barricade any open pilot holes.",
        "Secure loose pile sections against rolling (chocked or racked).",
        "Cover or flag any exposed anchor bolts.",
        "Restore or maintain traffic control devices overnight; confirm night-work lighting if the site "
        "remains active.",
        "Remove or secure unattended equipment; lock out idle torque heads and cranes.",
    ])


# --------------------------------------------------------------------
# 10. Equipment inspection and maintenance
# --------------------------------------------------------------------
def _section10_equipment(doc):
    _h(doc, "10. Equipment Inspection and Maintenance")
    _table(doc, ["Equipment", "Inspection frequency", "Out-of-service trigger"], [
        ("Torque head and drive shaft", "Daily pre-shift, plus manufacturer's preventive-maintenance "
         "schedule [verify interval]", "Missing/damaged guarding, hydraulic leak, or damaged reaction arm"),
        ("Hoses and hydraulics", "Daily visual, plus pressure test per manufacturer interval "
         "[verify]", "Visible bulge, abrasion exposing reinforcement, or any leak"),
        ("Rigging and slings", "Before each lift, plus documented periodic inspection per 29 CFR 1926.251 "
         "[verify clause]", "Deformation, crack, or wear exceeding the manufacturer's limit"),
        ("Crane", "Daily pre-operational per 29 CFR 1926.1412, plus annual certification [verify clause]",
         "Any deficiency affecting safe operation, until corrected by a qualified person"),
        ("Aerial lift", "Daily pre-operational per the manufacturer's checklist", "Any hydraulic or "
         "structural defect"),
    ])
    _p(doc, "An out-of-service trigger above removes the equipment from service immediately and tags it; "
            "it does not return to service until inspected and cleared by a qualified person.", bold=True,
        size=10)


# --------------------------------------------------------------------
# 11. Emergency response plan
# --------------------------------------------------------------------
def _section11_emergency(doc):
    _h(doc, "11. Emergency Response Plan")
    _table(doc, ["Scenario", "Immediate action"], [
        ("Underground utility strike — electrical", "Do not touch equipment or the struck line; keep "
         "everyone clear; if a vehicle/equipment is in contact with an energized line, occupants stay "
         "inside unless fire or life-threat requires evacuation, in which case jump clear (do not step "
         "down and touch ground and equipment simultaneously); call the utility emergency line and local "
         "emergency services."),
        ("Underground utility strike — gas", "Stop work immediately; eliminate ignition sources; "
         "evacuate upwind and uphill; call the gas utility emergency line and local emergency services."),
        ("Electrical contact (person)", "Do not touch the victim until the circuit is confirmed "
         "de-energized; call emergency services; begin CPR/AED if trained, once contact is confirmed "
         "safe."),
        ("Suspended-load incident", "Sound the alarm; clear the area; do not attempt to manually stabilize "
         "the load; call emergency services; preserve the scene for investigation (Section 12)."),
        ("Pole drop", "Clear the area; account for all personnel; call emergency services; do not attempt "
         "to right or move the pole."),
        ("Aerial-lift rescue", "Self-rescue is preferred where the worker is able; if incapacitated, use "
         "the ground-level emergency lowering control per the rescue plan (Section 5); never leave a "
         "suspended or incapacitated worker unattended."),
        ("Medical evacuation", "First-aid/CPR-trained personnel render aid; call local emergency services; "
         "clear access to the muster point for emergency vehicles."),
    ])
    _kv_table(doc, [
        ("Muster point", "[project-specific — confirm with Site Safety Officer before mobilization]"),
        ("Emergency contacts (utility, site office, etc.)", "[project-specific — confirm before "
         "mobilization]"),
        ("Nearest trauma facility", "[project-specific — confirm before mobilization]"),
        ("Who calls emergency services", "The Site Safety Officer or the most senior person present "
         "designates a caller, but every worker is empowered to call emergency services directly without "
         "seeking permission first."),
    ])


# --------------------------------------------------------------------
# 12. Incident reporting and investigation
# --------------------------------------------------------------------
def _section12_incident(doc):
    _h(doc, "12. Incident Reporting and Investigation")
    _bullets(doc, [
        "Reportable thresholds per the jurisdiction's recordkeeping regulation (e.g., 29 CFR 1904 for US "
        "OSHA [verify clause]): fatality reported within 8 hours; in-patient hospitalization, amputation, "
        "or loss of an eye reported within 24 hours [jurisdiction-specific — confirm exact clause "
        "and timeline].",
        "Near-miss capture: mandatory, no-blame, logged within 24 hours of occurrence.",
        "Root cause method: 5-Why or fishbone analysis (practice-based default), documented for every "
        "recordable incident and every significant near-miss.",
        "Corrective action closure: every corrective action is tracked to completion with a named owner "
        "and due date, and verified closed by the Site Safety Officer before the item is considered "
        "resolved.",
    ])


# --------------------------------------------------------------------
# 13. Audit, inspection, compliance monitoring
# --------------------------------------------------------------------
def _section13_audit(doc):
    _h(doc, "13. Audit, Inspection, and Compliance Monitoring")
    _table(doc, ["Activity", "Frequency", "Basis"], [
        ("Pre-shift equipment inspection + site walk", "Daily", "Section 9/10 checklists"),
        ("Formal documented site safety inspection", "Weekly (practice-based default)", "This procedure's "
         "hazard register (Section 5)"),
        ("JHA/permit audit", "Weekly (practice-based default)", "Section 4/6 registers"),
    ])
    doc.add_heading("Indicators tracked", level=2)
    _bullets(doc, [
        "Leading: JHA completion rate, near-miss reports filed, tailgate-briefing completion rate, PPE "
        "compliance observations.",
        "Lagging: recordable incident rate, lost-time incident rate, first-aid case count.",
    ])


# --------------------------------------------------------------------
# 14. Document control and records retention
# --------------------------------------------------------------------
def _section14_records(doc):
    _h(doc, "14. Document Control and Records Retention")
    _table(doc, ["Record", "Retention", "Custodian"], [
        ("JHAs, permits, tailgate briefings, inspection checklists",
         "[jurisdiction-specific — confirm against governing recordkeeping regulation, e.g. 29 CFR "
         "1904 retention is commonly 5 years in the US]", "Contractor safety department"),
        ("Training/competency/certification records", "For the duration of the individual's assignment "
         "to this project, plus the jurisdiction's retention period thereafter [jurisdiction-specific]",
         "Contractor safety department"),
        ("Incident reports and investigations", "[jurisdiction-specific — confirm against governing "
         "recordkeeping regulation]", "Site Safety Officer"),
        ("Crane/rigging inspection and certification records", "For the life of the equipment's "
         "assignment to this project, plus [jurisdiction-specific] years thereafter", "Equipment "
         "owner/Contractor"),
    ])


# --------------------------------------------------------------------
# Final checklist
# --------------------------------------------------------------------
def _final_checklist(doc, ctx, s):
    doc.add_page_break()
    _h(doc, "Pre-Mobilization Safety Readiness Checklist")
    _p(doc, "One page. All items must be checked by the Site Safety Officer before the first crew member "
            "mobilizes to site.", italic=True, size=9.5)
    rows = [
        ("Utility locate requested and locate tickets on file for every planned pile location", "□"),
        ("Overhead utility survey complete; MAD established for every line present (Section 5)", "□"),
        ("Lift plan reviewed and approved for pole erection; critical-lift permit obtained if triggered "
         "(Section 6)", "□"),
        ("Rigging inspected and certified for this project's loads", "□"),
        ("Crane operator, signal person, and rigger certifications verified and on file", "□"),
        ("Temporary traffic control plan approved, if the site requires one (Section 5)", "□"),
        ("Flagger(s) certified and scheduled, if required", "□"),
        ("Qualified Electrical Worker(s) identified for termination work", "□"),
        ("Hot work permit process established for field welding/galvanizing touch-up", "□"),
        ("PPE matrix (Section 8) stock confirmed on site, including upgraded PPE for energized/hot work",
         "□"),
        ("Emergency response plan muster point, contacts, and nearest trauma facility confirmed "
         "(Section 11)", "□"),
        ("All crew have received site-specific orientation and the first tailgate briefing", "□"),
        ("JHAs completed and approved for every task in the work sequence (Section 4)", "□"),
    ]
    _table(doc, ["Item", "Complete"], rows)
    doc.add_paragraph()
    _kv_table(doc, [
        ("Site Safety Officer sign-off (name / date)", ""),
        ("Contractor representative sign-off (name / date)", ""),
        ("Owner's Representative acknowledgment (name / date)", ""),
    ])
