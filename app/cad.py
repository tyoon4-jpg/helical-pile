"""
CAD export -- assembles a DXF pile-configuration drawing (elevation +
connection plan) from the current session's already-computed geometry.

Purpose
-------
Pure presentation, same as report.py: draws the geometry the sidebar
inputs already define (shaft OD, helix diameters/depths, bolt circle). It
duplicates no calculation logic and performs no design checks of its own.
"""
from __future__ import annotations

import io
import math

import ezdxf

LAYERS = {
    "GRADE": 3,        # green
    "FROST": 4,        # cyan
    "SHAFT": 7,         # white/black
    "HELIX": 1,          # red
    "CONNECTION": 5,   # blue
    "BOLTS": 6,          # magenta
    "TITLE": 7,
    "DIMENSIONS": 8,
}


def build_pile_configuration_dxf(ctx: dict) -> bytes:
    """Build a DXF drawing: pile elevation (shaft, helices, ground/frost
    lines, cap plate) plus a connection plan view (bolt circle). All
    drawing units are millimeters.
    """
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    for name, color in LAYERS.items():
        doc.layers.add(name=name, color=color)

    dimstyle = doc.dimstyles.get("EZDXF")
    dimstyle.dxf.dimtxt = 60
    dimstyle.dxf.dimasz = 40
    dimstyle.dxf.dimexe = 20
    dimstyle.dxf.dimexo = 20

    d_shaft_mm = ctx["d_shaft_mm"]
    reveal_mm = ctx["reveal_m"] * 1000.0
    d_f_mm = ctx["d_f_m"] * 1000.0
    L_pile_mm = ctx["L_pile_m"] * 1000.0
    helices = list(zip(ctx["helix_diam_mm"], [z * 1000.0 for z in ctx["helix_depth_m"]]))
    bcr_mm = ctx["bolt_circle_r_mm"]
    n_bolts = ctx["n_bolts"]
    bolt_r_mm = ctx["bolt_diam_mm"] / 2.0

    x0 = 0.0
    r_shaft = d_shaft_mm / 2.0
    span = max(d_shaft_mm, max(d for d, _ in helices)) * 1.8
    plate_r = max(bcr_mm * 1.25, r_shaft * 1.4)

    # -- Ground and frost lines ----------------------------------------
    msp.add_line((x0 - span, 0), (x0 + span, 0), dxfattribs={"layer": "GRADE"})
    msp.add_text("GRADE", dxfattribs={"layer": "GRADE", "height": 60}).set_placement(
        (x0 + span + 40, -20))

    msp.add_line((x0 - span, -d_f_mm), (x0 + span, -d_f_mm),
                 dxfattribs={"layer": "FROST", "linetype": "DASHED"})
    msp.add_text(f"FROST DEPTH df = {d_f_mm / 1000:.2f} m",
                 dxfattribs={"layer": "FROST", "height": 50}).set_placement(
        (x0 + span + 40, -d_f_mm - 20))

    # -- Shaft ------------------------------------------------------------
    msp.add_line((x0 - r_shaft, reveal_mm), (x0 - r_shaft, -L_pile_mm), dxfattribs={"layer": "SHAFT"})
    msp.add_line((x0 + r_shaft, reveal_mm), (x0 + r_shaft, -L_pile_mm), dxfattribs={"layer": "SHAFT"})
    msp.add_line((x0 - r_shaft, -L_pile_mm), (x0 + r_shaft, -L_pile_mm), dxfattribs={"layer": "SHAFT"})

    # -- Cap plate (connection, seen edge-on) ------------------------------
    msp.add_line((x0 - plate_r, reveal_mm), (x0 + plate_r, reveal_mm),
                 dxfattribs={"layer": "CONNECTION", "lineweight": 35})

    # -- Helices (plate seen edge-on, with flight ticks to the shaft) -----
    for i, (d_h, z) in enumerate(helices, start=1):
        r_h = d_h / 2.0
        msp.add_line((x0 - r_h, -z), (x0 + r_h, -z), dxfattribs={"layer": "HELIX", "lineweight": 50})
        msp.add_line((x0 - r_h, -z), (x0 - r_shaft, -z + 60), dxfattribs={"layer": "HELIX"})
        msp.add_line((x0 + r_h, -z), (x0 + r_shaft, -z + 60), dxfattribs={"layer": "HELIX"})
        msp.add_text(f"H{i}: dia {d_h:.0f} mm @ {z / 1000:.2f} m",
                     dxfattribs={"layer": "HELIX", "height": 50}).set_placement(
            (x0 + r_h + 60, -z - 15))

    # -- Dimensions: total pile length, frost depth ------------------------
    dim1 = msp.add_linear_dim(base=(x0 - span - 150, 0), p1=(x0, reveal_mm), p2=(x0, -L_pile_mm),
                               angle=90, dimstyle="EZDXF", dxfattribs={"layer": "DIMENSIONS"})
    dim1.render()
    dim2 = msp.add_linear_dim(base=(x0 - span - 300, 0), p1=(x0, 0), p2=(x0, -d_f_mm),
                               angle=90, dimstyle="EZDXF", dxfattribs={"layer": "DIMENSIONS"})
    dim2.render()

    # -- Connection plan view (offset to the right of the elevation) ------
    plan_cx = x0 + span * 3 + plate_r
    plan_cy = 0.0
    msp.add_circle((plan_cx, plan_cy), plate_r, dxfattribs={"layer": "CONNECTION"})
    msp.add_circle((plan_cx, plan_cy), r_shaft, dxfattribs={"layer": "SHAFT", "linetype": "DASHED"})
    for i in range(n_bolts):
        ang = 2 * math.pi * i / n_bolts
        bx = plan_cx + bcr_mm * math.cos(ang)
        by = plan_cy + bcr_mm * math.sin(ang)
        msp.add_circle((bx, by), bolt_r_mm, dxfattribs={"layer": "BOLTS"})
    msp.add_text(
        f"CONNECTION PLAN -- {n_bolts} bolts, dia {ctx['bolt_diam_mm']:.0f} mm, "
        f"BC radius {bcr_mm:.0f} mm",
        dxfattribs={"layer": "CONNECTION", "height": 50},
    ).set_placement((plan_cx - plate_r, plan_cy - plate_r - 100))

    # -- Title block --------------------------------------------------------
    title_x = x0 - span - 500
    title_y = reveal_mm + 400
    lines = [
        f"HELICAL PILE CONFIGURATION -- {ctx.get('project_name') or 'UNTITLED PROJECT'}",
        f"Location: {ctx.get('project_location', '')}   Engineer: {ctx.get('engineer_name', '')}   "
        f"Date: {ctx.get('calc_date', '')}",
        f"Shaft: {d_shaft_mm:.0f} mm OD x {ctx['t_nominal_mm']:.1f} mm wall nominal, "
        f"tip depth {L_pile_mm / 1000:.2f} m, {len(helices)} helix(es)",
        "SCHEMATIC ONLY -- generated from calc-engine inputs. NOT FOR CONSTRUCTION until "
        "independently verified and stamped.",
    ]
    for i, line in enumerate(lines):
        msp.add_text(line, dxfattribs={"layer": "TITLE", "height": 55 if i == 0 else 45}
                     ).set_placement((title_x, title_y - i * 70))

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")
