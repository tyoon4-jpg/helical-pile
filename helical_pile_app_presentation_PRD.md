# PRD — Presentation: "Using the Helical Pile Foundation Design App"

| Field | Value |
|---|---|
| Document type | Product Requirements Document (presentation deliverable) |
| Product presented | `helical-pile-design` — calculation engine + Streamlit desktop app + mobile web calculator |
| Presenter | TaeYang (developer / Engineer of Record perspective) |
| Audience | Company design engineers and field construction engineers |
| Duration | 40 minutes (35 min content + 5 min Q&A) |
| Format | Slides + live demo (desktop app) + live/recorded demo (mobile page) |
| Source documents | `README.md`, `workflow.md`, *Design Procedure: Helical Pile Foundations for Lighting Poles* |
| Status | Draft v0.2 — 2026-10-18 (open issues O1–O5 resolved against the code) |
| Scope note | This PRD defines the presentation only. No app functions are added or changed. |

---

## 1. Background

The company now has a tested Python calculation engine for helical pile foundations under lighting poles, built 1:1 on the 10-step design procedure (Loads → Geotech → Sizing → Axial → Lateral p-y → Structural → Corrosion → Connection → Torque → QA/QC). On top of it sit:

- A **Streamlit desktop app** that opens on a 3-agent dashboard (Design, Construction & QA/QC, Site Safety). The Design agent has live inputs (A1–A18), pass/fail capacity ratios, and p-y charts.
- Three **Word exports**: Calc Package, Construction & QA/QC Procedure, Site-Safety Procedure — plus a **CAD drawing** (`.dxf`, `app/cad.py`) from the Design agent.
- A **mobile web calculator** (`app/mobile.html`, GitHub Pages) for quick field checks.

Engineers do not yet know how to install it, run it, read its outputs, or where its limits are. This presentation closes that gap.

## 2. Problem statement

| Audience | Current pain | What the presentation must fix |
|---|---|---|
| Design engineers | Hand calcs / spreadsheets per pole; p-y runs separate from axial, corrosion, connection checks; arithmetic slips go unnoticed | Show one input set → full 10-step chain → signed-off calc package, with traceability to the procedure |
| Field construction engineers | Termination criteria, torque logs, and hold points arrive as scattered notes; torque is sometimes treated as proof of lateral capacity | Show the Construction & QA/QC export, the **torque AND depth** rule, and the mobile calculator for site use |

## 3. Goals and non-goals

### 3.1 Goals

| # | Goal |
|---|---|
| G1 | Every attendee can explain what the app does and does not do in one sentence. |
| G2 | Design engineers can install, launch, and run the worked example unaided after the session. |
| G3 | Design engineers can read the key outputs: capacity ratios, `y_gl`, `θ_gl`, pushover FS, `M_max`, `T_min`. |
| G4 | Field engineers can find and apply the termination criteria (minimum torque **and** minimum depth **and** torque cap) and the per-pile log. |
| G5 | Field engineers can open the mobile calculator on a phone and run a check. |
| G6 | Everyone understands responsibility boundaries: the app is a tool; assumptions and final design remain with the Engineer of Record. |

### 3.2 Non-goals

- Teaching helical pile theory, Broms, or p-y derivation in depth (reference the procedure document instead).
- Code walkthroughs of the Python modules.
- New features, UI changes, or bug fixes during or for the session.
- The future FastAPI/React productization path (mention only as one line in the roadmap).

## 4. Audience personas

| Persona | Background | Primary questions | Must leave with |
|---|---|---|---|
| **P1 — Design engineer** | Runs foundation calcs, prepares submittals, comfortable with Python at a basic level or not at all | "Can I trust the numbers? How do I change soil/wind? What goes into my report?" | Install steps, input→output map, calc package export, verification story (regression tests) |
| **P2 — Field construction engineer** | Supervises installation, signs torque logs, handles NCRs | "When do I stop installing? What do I record? What if I hit refusal?" | Termination rule, Installation Log, ITP/hold points, mobile calculator link (QR) |
| **P3 — Lead / manager (secondary)** | Approves tool adoption | "Is it auditable? What are the risks?" | Traceability, test suite, limitations list |

## 5. Key messages (repeat in opening and closing)

1. **One input set, ten checks, one document.** Sidebar inputs map to procedure assumptions A1–A18; every step runs live.
2. **Moment governs, not axial.** Lateral/moment (Step 5) is the governing check for light poles.
3. **Torque verifies axial capacity only.** It never waives minimum depth — the field rule is torque AND depth.
4. **The app formats; the library calculates.** No calculation logic lives in the UI; fixes go to the library and its regression test.
5. **Assumptions are defaults, not design.** Every A1–A18 value must be confirmed with project data before issue.

## 6. Agenda and timing (40 min)

| # | Time | Min | Section | Mode | Primary audience |
|---|---|---|---|---|---|
| 1 | 00:00–03:00 | 3 | Opening — why this tool | Slides | All |
| 2 | 03:00–08:00 | 5 | What's inside — 10 steps, architecture, verification | Slides | All |
| 3 | 08:00–11:00 | 3 | Install and launch (+ gotchas) | Slides + terminal | P1 |
| 4 | 11:00–23:00 | 12 | Live demo — desktop app, worked example | Live demo | P1 (P2 watch Step 9) |
| 5 | 23:00–28:00 | 5 | Exports — Calc Package, Construction & QA/QC, Site-Safety | Live demo | P1 + P2 |
| 6 | 28:00–32:00 | 4 | Mobile calculator for field use | Phone mirror / recording | P2 |
| 7 | 32:00–35:00 | 3 | Limits, responsibility, how to report issues | Slides | All |
| 8 | 35:00–40:00 | 5 | Q&A | Open | All |

Buffer rule: if the demo runs long, cut Section 5 to the Calc Package only and show the other two exports as screenshots.

## 7. Section requirements

### Section 1 — Opening (3 min)

- **Content:** Typical 12 m roadway pole; current workflow pain (hand calcs, scattered checks); what the app replaces.
- **Visual:** One slide: before (spreadsheets + separate LPILE + manual report) vs. after (one app → three documents).
- **Takeaway:** Key messages 1 and 5.

### Section 2 — What's inside (5 min)

- **Content:**
  - 10 procedure steps ↔ 10 modules (table from README).
  - Layering: library (`src/`) → desktop app / exports → mobile port.
  - Verification: regression suite locked to the Section 11 worked example; any failing test = correctness regression, not a tolerance to loosen.
  - Credibility example: building the tests caught two errors in the procedure document (Broms Hu 27 → 32.4 kN; Section 3.1 sizing coefficient). Conclusions unchanged.
- **Visual:** Step-to-module flow diagram; small table of the two corrected findings.
- **Takeaway:** Key message 4; "the tool is traceable and tested."

### Section 3 — Install and launch (3 min)

- **Content (commands shown on slide, not executed live unless time permits):**

  ```bash
  python -m pip install -e ".[app]"
  python -m pytest tests/ -v                     # 19 tests, ~4 s
  python examples/run_worked_example.py
  python -m streamlit run app/streamlit_app.py   # opens http://localhost:8501
  ```

- **Gotchas slide (must include all three):**

  | Symptom | Cause | Fix |
  |---|---|---|
  | Tests or app hang for minutes | OpenBLAS thread oversubscription on many-core PCs | Already pinned in tests, demo script, and app. In your own scripts set `OPENBLAS_NUM_THREADS=1` **before** importing numpy |
  | "Module not found" after install | `pip` and `python` point to different interpreters | Always use `python -m pip`; check with `python -c "import sys; print(sys.executable)"` |
  | `pytest` / `streamlit` not recognized | Scripts folder not on PATH in old terminals | Open a new terminal, or use `python -m pytest` / `python -m streamlit` |

- **Takeaway:** "Use `python -m` for everything."

### Section 4 — Live demo: desktop app (12 min)

Demo scenario = procedure Section 11 worked example (12 m pole, medium-stiff clay, Su = 50 kPa). Expected values are listed so the presenter can confirm the screen matches.

| Step | Time | Action on screen | Point to make | Expected value |
|---|---|---|---|---|
| 4.0 | 0.5 min | Dashboard → **Open Design** | Three agents; Construction and Site Safety auto-fill from Design's last result | — |
| 4.1 | 1.5 min | Walk the sidebar: pole, wind, soil, frost, corrosion, Kt groups | Each input = one A1–A18 assumption | Defaults = A1–A18 |
| 4.2 | 1.5 min | Step 1 results | Moment-dominant: e = M/V is large | V_u ≈ 2.75 kN, M_u ≈ 20.4 kN·m, e ≈ 7.4 m |
| 4.3 | 1.5 min | Step 3–4 results | Trial pile and axial; frost uplift governs tension | 273×9.3 pipe, 2×450 helices, tip 4.5 m; uplift FS ≈ 4.4 (with sleeve) |
| 4.4 | 3 min | Step 5 charts: deflected shape, moment, pushover | Frost zone has zero resistance; M_max just below frost; toe kick-back = adequate embedment | Service y_gl ≈ 1.92 mm, θ_gl ≈ 0.100°; strength M_max ≈ 23.8 kN·m at ≈1.3 m; pushover λ_ult ≈ 9.5–10 |
| 4.5 | 1 min | Step 6–8 | Corroded section used; connection checks wired in | H1 ratio ≈ 0.17; bolt 68 vs 103 kN |
| 4.6 | 1.5 min | Step 9 torque (**call field engineers' attention**) | Torque AND depth; torque never waives depth; Kt is assumed until validated | T_min ≈ 5.9 kN·m, tip ≥ 4.50 m |
| 4.7 | 2 min | "What-if": lower Su (e.g. 50 → 20 kPa) or bare steel in frost zone (no sleeve) | Badges turn red; show how the app tells you *why* | Ratios change live; buckling trigger appears if Su < 25 kPa |

- **Requirements:**
  - App pre-launched and warmed up before the session (first p-y run cached).
  - Browser zoom ≥ 125% so charts read from the back of the room.
  - Reset sidebar to defaults after the what-if step.
- **Takeaway:** Key messages 2 and 3.

### Section 5 — Document exports (5 min)

| Export | Who uses it | Show | Point to make |
|---|---|---|---|
| Calc Package (`app/report.py`) — Design page, **Generate calc package** | P1 | Cover, one-page pass/fail checklist, Step 1–10 detail with Step 5 charts | Auto-filled from current sidebar; no new calculation. **Generate CAD drawing** (`.dxf`) sits next to it — mention in one line |
| Construction & QA/QC Procedure (`app/construction_qaqc.py`) — **Continue to Construction & QA/QC agent** | P2 | Hold points, installation sequence, termination rule, ITP, per-pile Installation Log, NCR, Final Acceptance Checklist | Separate agent page; pile config, torque, and depth auto-fill from Design (editable). Adds construction-only inputs (Owner/AHJ, quantity, obstructions, utility density) |
| Site-Safety Procedure (`app/site_safety.py`) — **Continue to Site Safety agent** | P2 + safety | Hazard register, permits/hold points, PPE matrix, tailgate briefing, emergency plan, readiness checklist | Separate agent page; pole data auto-fills from Design. Adds safety-only inputs (jurisdiction, site type, traffic, overhead lines, lifting, crew); references, not restates, the other two documents |

- **Requirement:** Generate all three once before the session; open the pre-generated files if live generation is slow.
- **Takeaway:** "These documents are starting points; the Engineer of Record's project-specific direction governs."

### Section 6 — Mobile calculator (4 min)

- **Content:**
  - Link + QR code: `https://tyoon4-jpg.github.io/helical-pile/app/mobile.html`
  - Same calc chain, ported to JavaScript; cross-checked to the Python worked example.
  - Covers live checks only — **no** `.docx` exports and **no** `.dxf` CAD export (desktop only).
  - Field use case: quick check of `T_min` and minimum depth when conditions differ from the plan; escalate to the designer, do not redesign on site.
- **Requirement:** Invite attendees to open the QR link on their phones during this section (confirm site Wi-Fi/cell access).
- **Takeaway:** "Phone = quick check. Desktop = design and documents."

### Section 7 — Limits and responsibility (3 min)

Must cover:

1. **Assumptions A1–A18 are typical values** and must be replaced with project data.
2. **Kt = 7 m⁻¹ is assumed** — validate per AC358 report or ASTM D3689 before production.
3. **Bolt bending uses nominal-diameter section modulus** — underestimates bending stress; use the manufacturer's thread-root modulus for final design.
4. **Mobile page is a hand port** — it does not auto-update with library fixes; re-verified after engine changes.
5. **Load-test triggers** in the worked example (assumed Kt, SPT-derived Su/ε50) → one pre-production pile with D3689 + D3966.
6. **Reporting issues:** describe inputs + expected vs. actual; fixes go into the library and its regression test, never the UI.

### Section 8 — Q&A (5 min)

Prepared answers (backup slides):

| Likely question | Short answer |
|---|---|
| Can it replace LPILE? | It uses the same beam-on-nonlinear-Winkler formulation and is cross-checked, but production designs should be reproduced with a QA'd program per the procedure. |
| Can it handle sand / layered soil? | State current support honestly; refer to Step 2 and roadmap. |
| Why is FS 11.8 by Broms but ~10 by pushover? | Simplified closed form vs. full nonlinear pushover; ~20% spread is reasonable; both ≫ 2.0. |
| Can field staff change the design on the phone? | No. Mobile is for checks; changes go through the designer. |
| What if torque is reached before minimum depth? | Keep advancing to minimum depth within the torque cap; refusal above minimum depth → engineer's direction (predrill/relocate). |
| Is it ASCE 7 or LTS-6? | LTS-6 by default; don't mix frameworks in one calc. |

## 8. Deliverables for the session

| # | Item | Owner | Format |
|---|---|---|---|
| D1 | Slide deck (≈18–22 slides incl. backups) | Presenter | Slides |
| D2 | Demo environment (installed, tested, app warmed up) | Presenter | Laptop |
| D3 | Pre-generated exports (3 × `.docx`) | Presenter | Word |
| D4 | One-page handout: install commands, gotchas, termination rule, mobile QR | Presenter | PDF / print |
| D5 | Backup screen recording of Sections 4 and 6 | Presenter | Video |
| D6 | Feedback form (3 questions) | Presenter | Form / paper |

## 9. Pre-session checklist

- [ ] `python -m pytest tests/ -v` passes on the demo laptop (all green, a few seconds).
- [ ] `python examples/run_worked_example.py` prints the full report.
- [ ] App launches with `python -m streamlit run app/streamlit_app.py`; first run done.
- [ ] Demo values on screen match Section 4 expected values.
- [ ] All three exports generate and open in Word.
- [ ] Mobile page loads on venue network; QR code tested.
- [ ] Backup recording on local disk (no network dependency).
- [ ] Projector resolution / zoom checked for charts.

## 10. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| p-y solver hangs (OpenBLAS threading) | Demo stalls | Launch via provided entry points (already pinned); backup recording |
| Wrong interpreter / missing package | App won't start | `python -m` commands; rehearse on the exact laptop |
| Venue network blocks GitHub Pages | Mobile demo fails | Screen recording + QR handout for later |
| Export generation slow or Word missing | Section 5 overruns | Open pre-generated files |
| Audience treats defaults as design values | Misuse after session | Key message 5 in opening and closing; Section 7 |
| Field staff read torque as lateral proof | Unsafe installations | Key message 3 repeated in Sections 4.6, 5, 6 |

## 11. Success metrics

| Metric | Target | Measured by |
|---|---|---|
| Design engineers who run the worked example within 1 week | ≥ 80% | Follow-up check |
| Attendees who correctly state the termination rule (torque AND depth AND cap) | ≥ 90% | Feedback form Q1 |
| Attendees who correctly state that Kt / A1–A18 are assumptions to validate | ≥ 90% | Feedback form Q2 |
| Session on time | 40 min ± 2 | Timer |
| Overall usefulness rating | ≥ 4 / 5 | Feedback form Q3 |

## 12. Acceptance criteria for the presentation

1. All eight sections delivered within the 40-minute budget.
2. Live demo shows Step 1, Step 5 charts, and Step 9 values matching the worked example.
3. All three exports shown (live or pre-generated).
4. Mobile link shared and accessible to attendees.
5. Limitations in Section 7 stated explicitly — none omitted.

## 13. Open issues — resolution log

Checked against the code and test run on 2026-10-18.

| # | Item | Finding | Resolution |
|---|---|---|---|
| O1 | Calc-package button label | Section heading is "Calc package export"; the button is **"Generate calc package"** (`app/streamlit_app.py`) | Slides use "Generate calc package". README wording corrected |
| O2 | Streamlit launch command | Both forms work; `python -m` works regardless of PATH | Teach `python -m streamlit run …`. workflow.md corrected |
| O3 | Mobile calculator location | `app/mobile.html` is in the repo, served via GitHub Pages | Present the GitHub Pages link. workflow.md corrected |
| O4 | Regression test count | `python -m pytest tests/ -q` → **19 passed in 3.9 s** | Quote "19 tests, ~4 s" |
| O5 | `.dxf` CAD export | Exists: `app/cad.py`, **"Generate CAD drawing"** button on the Design page | Mention in Sections 5 and 6 (desktop only) |
| O6 | Presentation language | Decided 2026-10-18 | Korean slides; technical terms, UI labels, commands, and symbols stay in English |
| O7 | App structure (new) | App opens on a 3-agent dashboard; Construction and Site-Safety exports live on their own agent pages, not in Design-sidebar expanders | Demo step 4.0 added; Section 5 table updated |
