# PRD Framework: Optimizing Helical Pile Foundations for Light Poles

**Document Type:** Product Requirement Document — Structural Layout & Authoring Guide
**Purpose:** Defines *what each section must contain*. This is the skeleton to be populated by the engineering team — not the final content.

---

## 1. Document Control & Metadata

*Establishes traceability and accountability before any technical content.*

**This section must contain:**

- **Document ID & Title** — Unique identifier (e.g., `PRD-HPF-LP-001`), full project title.
- **Revision Table** — Version number, date, author, description of changes, approver. One row per revision. Rev 0 = initial issue for internal review; Rev A/1 = issued for use.
- **Author & Reviewer Matrix** — Name, role, and responsibility (RACI format recommended):
  - Geotechnical Engineer of Record (GEOR)
  - Structural Engineer of Record (SEOR)
  - Installation Contractor Representative
  - QA/QC Lead
  - Client / Owner's Engineer
- **Distribution List** — Who receives controlled copies; who receives informational copies.
- **Reference Document Register** — Numbered list of governing codes and standards cited throughout (ICC-ES AC358, IBC 2021 Ch. 18, AASHTO LTS-6, ASTM D1143/D3689/D3966, AISC 360, FHWA GEC-8 or equivalent). Every later section cites by register number, not by re-stating the standard.
- **Definitions & Abbreviations** — Kt (torque correlation factor), SPT, CPT, HDG (hot-dip galvanizing), FEA, ultimate vs. allowable capacity, etc.

---

## 2. Executive Summary

*One page maximum. Written last, placed first. Must be readable by a non-engineer project sponsor.*

**This section must contain:**

- **Problem in one sentence** — Why conventional light pole foundations (drilled concrete piers) are slow, weather-dependent, and excavation-heavy.
- **Proposed solution in one sentence** — Helical piles as a screw-in, immediately loadable, minimal-spoil alternative.
- **Three headline value propositions**, each with a quantifiable target placeholder:
  - *Speed:* installation time per foundation (target: e.g., < 30 min vs. multi-day cure).
  - *Immediate loading:* no concrete cure wait; pole erected same day.
  - *Minimal excavation:* no spoil haul-off, no dewatering, reduced utility strike exposure.
- **Research objective statement** — What this project will *produce* (validated torque-to-capacity correlations and selection charts specific to light pole loading).
- **High-level scope boundary** — One line on what is in/out (details deferred to Section 4).
- **Expected business/engineering impact** — Cost per foundation, schedule compression, design standardization.

---

## 3. Project Background & Problem Statement

*The "why now" section. Must justify the research investment technically.*

**This section must contain:**

- **Current state of practice** — How light pole foundations are designed today (drilled piers per AASHTO LTS / Broms method), and their pain points.
- **Governing load characteristics unique to light poles** — This is the technical crux and must be explicit:
  - **Low axial load, high overturning moment** — self-weight is trivial; wind on the luminaire and pole controls.
  - **Lateral wind loads** per ASCE 7-22 / AASHTO LTS wind maps, including gust and vortex-shedding fatigue considerations.
  - **Moment-to-shear ratio** — large eccentricity (load applied at pole top) makes this a *lateral/moment problem*, not an axial one. State why generic helical pile axial data is insufficient.
- **Frost heave problem definition** — Adfreeze uplift on shallow foundations; how helix depth below frost line resists heave; regional frost depth assumptions.
- **Knowledge gaps this research closes** — e.g.:
  - Published Kt values are axial-capacity-based; lateral/moment behavior of slender helical shafts is under-documented.
  - No standardized selection tool exists linking pole height → wind load → pile configuration → soil class.
- **Problem statement** — A single boxed paragraph: *"There is currently no validated, code-defensible method for selecting helical pile foundations for light poles of height X–Y m under wind loads per [standard], across soil classes [range]."*

---

## 4. Scope of Research

*Hard boundaries. Every future scope dispute is settled by this section.*

### 4.1 Included

**Each item below must have a one-line justification and a parameter range:**

- **Pile configurations** — Single-helix vs. multi-helix (2–3 plates); helix spacing ratios (typically 3D); plate diameters (e.g., 8"–14" / 200–350 mm).
- **Shaft types** — Round shaft vs. square bar; state which and why (round shaft preferred for lateral stiffness — justify).
- **Torque-to-capacity correlation (Kt)** — Empirical Kt derivation for the specific shaft sizes tested, in both tension and compression.
- **Soil types** — Define test matrix:
  - Cohesive (soft to stiff clay, undrained shear strength range)
  - Cohesionless (loose to dense sand, friction angle / SPT-N range)
  - Optional: mixed/layered profiles if budget permits — state decision.
- **Pole height range** — e.g., 6 m to 15 m (20–50 ft) roadway and parking lot poles.
- **Loading modes** — Axial compression, axial tension (frost/uplift), lateral, and combined moment-lateral.

### 4.2 Excluded

**Each exclusion must state the reason (risk, budget, or applicability):**

- Traditional concrete pad/pier foundations — baseline comparison only, not researched.
- High-mast towers above the defined height cutoff (e.g., > 15 m / 50 ft) — different wind regime, foundation class, and code path.
- Seismic-governed design cases (if wind governs in target regions — justify).
- Rock-socketed or grouted helical piles.
- Battered/inclined pile groups (unless a specific design concept in §5 requires them — flag as conditional).

---

## 5. Technical & Engineering Requirements

*The requirements backbone. Every requirement must be numbered (REQ-XXX), verifiable, and traceable to a test in Section 6.*

### 5.1 Helix & Shaft Geometry

- **Helix plate specifications** — Diameter range, thickness (min. per ICC-ES AC358), pitch (standard 3"), true helix form tolerance (avoids soil disturbance during installation).
- **Shaft specifications** — Diameter/wall thickness options (e.g., 2-7/8", 3-1/2", 4-1/2" OD pipe); slenderness limits for buckling in soft soils; lateral stiffness (EI) as a controlling parameter — must be stated explicitly given moment-dominant loading.
- **Coupling details** — Bolted coupling rigidity requirement (coupling slop degrades lateral/moment performance — require zero-gap or grouted couplings and say why).
- **Pole-to-pile connection** — New anchor bolt cage adapter / bolt circle compatibility with standard pole base plates; embedment and weld requirements.

### 5.2 Materials & Steel Grade

- Steel grades per ASTM A500/A252/A572 with minimum yield strength.
- Weld specifications (helix-to-shaft) per AWS D1.1.
- Mill certificate and traceability requirements.

### 5.3 Corrosion Protection

- **Design life target** — State it (e.g., 50 or 75 years) — everything follows from this number.
- **Hot-dip galvanizing** per ASTM A123 — minimum coating thickness, expected life vs. soil corrosivity class.
- **Sacrificial steel thickness allowance** per ICC-ES AC358 / soil resistivity classification.
- **Soil corrosivity testing requirements** — resistivity, pH, chlorides, sulfates thresholds that trigger enhanced protection.
- **Corrosion at the air-soil interface** — the critical zone for poles; specify additional protection detail.

### 5.4 Geotechnical Testing Parameters

- **Site characterization minimums** — SPT boring or CPT sounding depth (helix depth + 3–5 helix diameters), sampling interval.
- **SPT/CPT-to-torque correlations** — Required data pairs: N-value or qc profile vs. recorded installation torque at depth, for every test pile.
- **Torque measurement accuracy** — Calibrated torque indicator requirement (±5% or better, calibration certificate on file).
- **Minimum embedment criteria** — Frost depth + margin; minimum depth-to-helix-diameter ratio for "deep" failure mode.

### 5.5 Design Concepts

*The innovation sandbox — each concept documented in a standard template: sketch, mechanism, expected benefit, feasibility risk.*

**Must catalogue candidate concepts to be screened, e.g.:**

- Enlarged upper shaft section or bolted lateral-stiffening sleeve at grade to boost moment capacity.
- Dual-pile / small group cap for high-moment cases.
- Integrated anchor-bolt adapter cap eliminating field welding.
- Helix plate geometry variants (e.g., ribbed or cut-edge plates for cobble penetration).
- **Screening criteria** — Each concept scored on capacity gain, cost, installability, and patentability before advancing to §6 testing.

### 5.6 Patent Ideas

- **Prior art search requirement** — Freedom-to-operate review before field testing novel hardware.
- **Invention disclosure process** — Who documents, who reviews, filing decision gates.
- **Candidate patentable elements** — e.g., lateral-stiffening sleeve geometry, torque-correlated selection software/method, quick-connect pole adapter.
- **Confidentiality controls** — What can/cannot appear in published test reports prior to filing.

---

## 6. Testing & Validation Methodology

*Every REQ from Section 5 must map to at least one verification method here. Include a traceability matrix.*

### 6.1 Theoretical Modeling & FEA

- **Analysis tools & methods** — LPILE (p-y method) for lateral response; FEA (e.g., PLAXIS 3D) for soil-structure interaction and helix bearing mechanics; hand-calc baseline (individual bearing vs. cylindrical shear methods) for axial.
- **Load cases modeled** — ASCE 7-22 / AASHTO wind on tallest and shortest pole in scope; frost uplift; combined cases.
- **Model calibration plan** — FEA parameters to be back-calculated from field test results (Phase-gate: models updated after each field campaign).
- **Deflection criteria** — Serviceability limits at pole base (rotation and lateral translation limits — state values, since pole-top sway is the visible failure).

### 6.2 Field Testing Procedures

- **Test standards (mandatory citations):**
  - Axial compression — ASTM D1143
  - Axial tension — ASTM D3689
  - Lateral load — ASTM D3966
- **Test matrix definition** — Number of piles per configuration per soil site; minimum replicates for statistical validity (state n).
- **Test site requirements** — At least one cohesive and one cohesionless site, each with full SPT/CPT characterization.
- **Acceptance/failure criteria per test** — e.g., Davisson-type offset for axial; deflection limit at design load for lateral.
- **Instrumentation** — Load cells, dial gauges/LVDTs, inclinometers on shaft for lateral tests, strain gauges if load-transfer distribution is needed.

### 6.3 Real-Time Torque Monitoring

- **Continuous torque-vs-depth logging** — Digital recording (not just final torque); sampling rate; data format for later correlation analysis.
- **Calibration protocol** — Pre- and post-campaign calibration of torque indicators against a reference.
- **Installation records per pile** — Torque log, penetration rate, RPM, crowd pressure, obstruction events, final tip depth.
- **Termination criteria** — Minimum torque AND minimum depth both required (never torque alone — state this rule explicitly).

---

## 7. Success Criteria & Key Deliverables

*Binary, measurable definitions of "done."*

**This section must contain:**

- **D1 — Validated Kt correlations** — Empirical torque-to-capacity factors (tension and compression) per shaft size and soil class, with confidence intervals and comparison to published/AC358 default values.
- **D2 — Lateral/moment design method** — Calibrated p-y or equivalent procedure for helical shafts under pole loading, validated against ASTM D3966 results within a stated error band (e.g., predicted vs. measured within ±20%).
- **D3 — Standardized selection charts** — Matrix of: pole height × wind zone × soil class → pile configuration (shaft size, helix count/diameter, min. depth, min. torque). Format requirement: single-page chart usable by a designer without geotechnical software.
- **D4 — Installation specification** — Master spec section (CSI format) covering equipment, torque monitoring, termination, and QA records.
- **D5 — Research report** — Full data appendices, FEA calibration record, and limitations statement.
- **Quantitative success thresholds** — e.g., "≥ 90% of field tests meet or exceed torque-predicted capacity"; "selection chart covers ≥ 80% of standard DOT pole catalogue."

---

## 8. Constraints & Risks

*Each risk entered in a register: description, likelihood, impact, mitigation, owner.*

**This section must contain, at minimum:**

- **Installation equipment limitations** — Max torque of available drive heads vs. required torque in dense soils; machine access/reach on constrained sites; overhead clearance ironically limited by existing lighting/utilities.
- **Underground utility conflicts** — Locate requirements (call-before-you-dig), tolerance zones, and the mitigation advantage of helical piles (relocatable/reversible) — but also the risk of striking unlocatable utilities with a rotating pile.
- **Cobbles, boulders & obstructions** — Refusal criteria, pre-drilling allowance, offset-and-reinstall procedure, impact on Kt validity (disturbed torque readings must be flagged and excluded from correlation datasets).
- **Data risks** — Insufficient soil variability across test sites; torque indicator drift; small sample sizes undermining statistical claims.
- **Regulatory/code risk** — AHJ acceptance of helical foundations for public roadway poles; path to ICC-ES evaluation report if commercializing.
- **Schedule/budget risks** — Weather windows for field testing; steel lead times; lab/site availability.

---

## 9. Timeline & Milestones

*Phase-gated. Each phase lists entry criteria, activities, exit criteria (gate), and duration.*

**Required phase structure:**

- **Phase 0 — Literature Review & Gap Analysis** *(4–6 wks)*
  - Exit gate: Gap report approved; test matrix drafted.
- **Phase 1 — Design & Modeling** *(6–8 wks)*
  - Pile configurations designed; LPILE/FEA predictions issued; test piles fabricated.
  - Exit gate: Design review sign-off by SEOR + GEOR.
- **Phase 2 — Site Characterization** *(4 wks, can overlap Phase 1)*
  - SPT/CPT campaigns at both soil sites complete; corrosivity testing done.
  - Exit gate: Geotechnical data report issued.
- **Phase 3 — Field Installation & Load Testing** *(8–10 wks)*
  - All piles installed with torque logging; axial and lateral test program executed.
  - Exit gate: Raw test data QC'd and locked.
- **Phase 4 — Analysis & Model Calibration** *(6 wks)*
  - Kt derivation, FEA back-analysis, selection chart drafting.
  - Exit gate: Draft deliverables D1–D3 in internal review.
- **Phase 5 — Validation & Final Reporting** *(4 wks)*
  - Independent check, final report, patent filing decisions, spec publication.
  - Exit gate: All success criteria (§7) verified; project closeout.
- **Milestone summary table** — One-line-per-milestone with target dates and responsible party.
- **Critical path note** — Identify it explicitly (typically fabrication → field testing weather window).

---

## Authoring Rules (applies to whole document)

- Every requirement numbered and verifiable; every requirement traced to a §6 test.
- All capacities stated as ultimate vs. allowable with the factor of safety explicit.
- SI and imperial units dual-stated throughout.
- Figures required: pile configuration sketches (§5.1), test setup schematics (§6.2), example selection chart mockup (§7).
