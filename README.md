# helical-pile-design

Python calculation engine for helical pile foundations supporting lighting
poles. This is the calc-engine layer described in the architecture
recommendation: a UI (Streamlit, or later a React/FastAPI product) should
be built *on top of* this package, never with calculation logic duplicated
into the UI layer.

## Structure

Every module maps 1:1 to a numbered step in the governing design procedure
document ("Design Procedure: Helical Pile Foundations for Lighting
Poles"):

| Step | Module | Purpose |
|---|---|---|
| 1 | `loads.py` | Wind pressure, base reactions (V, M, P), load combinations |
| 2 | `geotech.py` | SPT/CPT correlations, design soil profile |
| 3 | `sizing.py` | Trial shaft/helix sizing, embedment checks |
| 4 | `axial.py` | Compression and tension/frost-uplift capacity |
| 5 | `lateral_py.py` | Broms preliminary check + validated p-y beam-spring solver |
| 6 | `structural.py` | AISC 360 shaft checks (corroded section) |
| 7 | `corrosion.py` | 75-year sacrificial thickness + HDG |
| 8 | `connection.py` | Anchor bolts, cap plate, weld |
| 9 | `torque.py` | Installation torque termination criteria |
| 10 | `qaqc.py` | Load-test trigger logic |

## Install

```bash
pip install -e ".[dev]"       # editable install + pytest
pip install -e ".[app]"       # add streamlit + plotly for a UI layer
```

## Run the regression suite

```bash
pytest tests/ -v
```

**Note on many-core machines:** the p-y solver (`lateral_py.solve_py`) does
repeated small (~360x360) dense linear solves -- up to hundreds of
iterations per load step, times up to 17 pushover load steps. On machines
with a high core count, OpenBLAS's default thread pool makes each solve
~280x slower (thread synchronization overhead dominates for a matrix this
small), turning a 3s test run into a multi-minute hang on
`test_pushover_matches_broms_cross_check`. `tests/conftest.py`,
`examples/run_worked_example.py`, and `app/streamlit_app.py` all pin
`OPENBLAS_NUM_THREADS=1` before numpy is imported to avoid this -- if you
import this package directly in your own script, set that env var first
too (setting it *after* numpy is already imported has no effect).

## Run the demo script (fastest way to see it work)

```bash
python examples/run_worked_example.py
```

Runs all 10 steps on the worked example and prints a readable report to
the console -- no UI required. This is the quickest way to confirm the
package works after installing it.

## Run the interactive app

```bash
pip install -e ".[app]"
python -m streamlit run app/streamlit_app.py
```

Opens in your browser (default `http://localhost:8501`). Every input in
the sidebar maps to an A1-A18 assumption from the design procedure
document; results, capacity ratios, and the p-y deflection/moment/pushover
plots update live. This app duplicates no calculation logic -- it only
calls into the library above, so any correctness fix belongs in the
library (and its regression test), not in `app/streamlit_app.py`.

The "Calc package export" button at the bottom of the page (see
`app/report.py`) generates a Word `.docx` -- cover page, one-page
pass/fail checklist, and Step 1-10 detail with the Step 5 charts embedded
as static images -- auto-filled from whatever is currently in the
sidebar. Like the rest of the app, it duplicates no calculation logic,
only formats already-computed results into a document.

## Mobile app

`app/mobile.html` is a self-contained, phone-friendly calculator -- open it
in any mobile browser, no install or server required:

https://tyoon4-jpg.github.io/helical-pile/app/mobile.html

It's a JavaScript port of the same calc chain (loads -> geotech -> sizing ->
axial -> lateral p-y -> structural -> corrosion -> torque -> connection ->
QA/QC), numerically cross-checked against the Python worked example --
matches to full float precision except for ~1e-10-level noise in the p-y
solver's iterative convergence. Because it's a hand port rather than a
direct call into the library, it will NOT automatically pick up future
fixes to `src/helical_pile_design`; re-verify it against
`tests/test_worked_example_12m.py` after any calc-engine change.

It covers the same live checks as the desktop app but not the `.docx`
calc-package or `.dxf` CAD export -- those stay desktop-only
(`app/streamlit_app.py`).

The page is served via GitHub Pages from this repo's `main` branch, which
requires the repo to be public.

The cylindrical-shear axial method (Step 4.2, `axial.cylindrical_shear_compression_kN`)
and the pole-to-pile connection design (Step 8, `connection.py` -- bolt
combined tension + standoff-bending stress, weld, and torsion slip checks)
are wired into the UI. The bolt bending term uses a solid-shank section
modulus (`connection.bolt_section_modulus_m3`) computed from the *nominal*
bolt diameter as a stand-in for the true thread-root diameter -- this
overestimates the section modulus and therefore underestimates the
bending stress; replace with the manufacturer's thread-root modulus
before final design.

`tests/test_worked_example_12m.py` locks the entire engine to the
independently cross-checked 12 m pole / medium-stiff-clay worked example
from the design procedure document (Section 11). **Any change to this
package should keep this suite green.** If it doesn't, treat that as a
correctness regression to investigate, not a tolerance to loosen.

## Findings from building this test suite

Writing the regression tests against the source document surfaced two
real issues in the document itself, now corrected in code (and flagged
here so the source document can be corrected too):

1. **Section 11.5.1 Broms hand calculation was arithmetically wrong.**
   `Hu = 27 kN` does not satisfy the document's own closure equation
   (`f + g` should equal 3.30 m; at `Hu=27` it equals 2.99 m). The
   correct root, verified by bisection and independently by brute-force
   sweep, is `Hu ~= 32.4 kN` (`FS ~= 11.8`, not `~9.8`). The design
   conclusion is unaffected — both the corrected Broms FS and the p-y
   pushover `lambda_ult ~= 9.5-10` clear the required FS = 2.0 by a wide
   margin — but the document's claimed "agreement within 3%" between the
   two methods should be corrected to reflect the wider (~20-25%) but
   still reasonable spread between a simplified closed-form method and a
   full nonlinear pushover.

2. **Section 3.1's shaft-sizing heuristic has a units/coefficient
   inconsistency.** `D_shaft >= sqrt(Mu/40)` gives `0.71 m` for the
   worked example's `Mu = 20.4 kN*m` — nowhere near the document's own
   stated typical range (168-324 mm) or the 273 mm shaft the worked
   example actually uses. `sizing.py` uses a corrected coefficient (320)
   calibrated to land in the stated range; like the original, it remains
   a rough starting point only, refined by the actual Steps 4-6 checks.

Neither finding changes the worked example's final pile selection or its
pass/fail conclusions — both were already governed by ample margins. This
is exactly the value of turning a procedure document into a tested
codebase: these are the kinds of small hand-arithmetic slips that don't
survive contact with an automated regression test.

## Design principles enforced by the module structure

- **SI units internally, everywhere.** Convert only at the display/report
  layer — don't let dual-unit logic leak into calculation functions.
- **Corroded, not nominal, section properties feed structural checks.**
  `structural.py` functions take `t_c` (corroded wall) by name; there is
  deliberately no `t_nominal` parameter to accidentally pass instead.
- **Every result carries its equation/citation basis**, not just a number
  — see each module's docstrings, which cite the specific doc section and
  equation. An app layer built on this package should surface that
  provenance to the user, not just the numeric output.
- **Ultimate vs. allowable/service is never conflated.** Factors of
  safety (`FS_AXIAL`, `FS_LATERAL_PRELIM`, `FS_PUSHOVER`, etc.) are
  explicit module-level constants or function parameters, never hidden
  inside a formula.

## Suggested next steps

The Streamlit app (sliders/inputs for A1-A18, live capacity ratios, plotly
charts), the "generate calc package" export (Word calc package + a
one-page pass/fail checklist, auto-filled from the current sidebar -- see
`app/report.py`), and the Step 8 bolt combined-stress check (tension +
standoff bending, `connection.bolt_check`) are all done.

Only after validating the MVP with real projects, consider the productized
path (FastAPI backend + React frontend, multi-project management, PDF
sealing) discussed in the architecture recommendation.
