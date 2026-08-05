# Workflow

Practical day-to-day commands for working with this repo. `README.md` covers
what the package is; this covers how to actually run things on a fresh
checkout, plus the machine-specific gotchas that aren't obvious from a
plain `pip install`.

## Setup

```bash
python -m pip install -e ".[dev]"    # editable install + pytest
python -m pip install -e ".[app]"    # + streamlit, plotly, python-docx, matplotlib
```

Use `python -m pip`, not bare `pip` -- on a machine with more than one
Python install on PATH (common on Windows), `pip` and `python` can silently
resolve to *different* interpreters, so packages land somewhere `python`
never sees. `python -m pip` always installs into the interpreter you're
about to run.

## Test

```bash
python -m pytest tests/ -v      # 19 tests, ~3.5s
```

If this hangs instead of finishing in a few seconds, see **OpenBLAS
thread oversubscription** below -- that's almost certainly it.

## Run the demo script

```bash
python examples/run_worked_example.py
```

Fastest way to see the whole 10-step calc chain run and print a report,
no UI needed.

## Run the interactive app

```bash
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501`. Every sidebar change reruns the calc
chain live. The "Generate calc package" button at the bottom exports a
Word `.docx` (cover page, one-page pass/fail checklist, Step 1-10 detail
with charts) built from whatever is currently in the sidebar.

## Known gotchas on this machine

**OpenBLAS thread oversubscription.** The Step 5 p-y solver does many
small (~360x360) linear solves. On a high-core-count machine, OpenBLAS's
default thread pool makes each solve ~280x slower (thread-sync overhead
dominates at this matrix size), turning a 3s test run into a multi-minute
hang. `tests/conftest.py`, `examples/run_worked_example.py`, and
`app/streamlit_app.py` all set `OPENBLAS_NUM_THREADS=1` *before numpy is
imported* to avoid this. If you write a new script that imports this
package directly, set that env var as the very first thing in the file --
setting it after numpy has already loaded has no effect.

**`python` vs `pip` resolve to different installs.** Confirmed on this
machine: bare `pip` resolves to a Python 3.13 install while `python`
resolves to 3.14. Always use `python -m pip`, and when in doubt confirm
with `python -c "import sys; print(sys.executable)"`.

**PATH.** Console scripts (`pytest.exe`, `streamlit.exe`, etc.) install to
a `Scripts` directory that's since been added to this user's PATH via the
registry -- takes effect in *new* terminal sessions only, not ones already
open. Until then, `python -m pytest` / `python -m streamlit` work
regardless of PATH state.

## Architecture (one-line version)

All calculation logic lives in `src/helical_pile_design/*.py`, one module
per numbered design-procedure step. `app/streamlit_app.py` and
`app/report.py` are presentation-only -- they call into the library and
format results, never recompute anything themselves. A correctness bug
always lives in `src/`, never in `app/`; `tests/test_worked_example_12m.py`
is the regression anchor for the whole engine.

There's also a standalone HTML/JS port of the full engine (published as a
Claude artifact, not part of this repo) for running the calculator with no
Python install at all -- same formulas, ported by hand and cross-checked
against this library's test values.
