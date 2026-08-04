"""
helical_pile_design
====================

Python calculation engine for helical pile foundations supporting lighting
poles. Every module maps 1:1 to a numbered step in the governing design
procedure document ("Design Procedure: Helical Pile Foundations for
Lighting Poles"), so a result can always be traced back to a specific
step, equation, and code citation.

STEP -> MODULE MAP
-------------------
 1  Load determination                    -> loads.py
 2  Geotechnical parameterization          -> geotech.py
 3  Preliminary pile sizing                -> sizing.py
 4  Axial capacity (compression/tension)   -> axial.py
 5  Lateral and moment capacity (p-y)      -> lateral_py.py
 6  Shaft structural checks (AISC 360)     -> structural.py
 7  Corrosion design (75-yr life)          -> corrosion.py
 8  Pole-to-pile connection design         -> connection.py
 9  Installation torque specification      -> torque.py
10  QA/QC and load test triggers           -> qaqc.py

Design philosophy carried into the code
----------------------------------------
- SI units internally, everywhere. Convert only at the display/report layer.
- Every function returns a dataclass carrying the *equation basis* and the
  code citation, not just a bare number -- so the app layer can always show
  its work.
- Ultimate vs. allowable/service capacity is never conflated: factors of
  safety are explicit parameters, never hidden defaults baked into a formula.
- The corroded (end-of-life) section property, not the nominal one, is what
  feeds the structural checks (Step 6) -- this is enforced by type, not by
  convention: structural.py takes a `t_c` argument, never `t_nominal`.
"""

from importlib.metadata import version as _version, PackageNotFoundError

try:
    __version__ = _version("helical-pile-design")
except PackageNotFoundError:  # pragma: no cover - local/editable checkout
    __version__ = "0.1.0-dev"

__all__ = ["__version__"]
