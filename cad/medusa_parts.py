"""Medusa 3D printed parts.

Run:  .venv/bin/python cad/medusa_parts.py
Writes one STL per part into cad/stl/.

All sizes are in millimetres. If a part does not fit, change the numbers in SETTINGS and run it again.
"""

from pathlib import Path

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, set_circular_segments

set_circular_segments(64)

# ---------------------------------------------------------------- SETTINGS
CLEAR = 0.4  # gap added around anything that has to slide in

# SG90 micro servo
SERVO_L, SERVO_W = 22.8, 12.2  # body footprint
FLANGE_Z = 15.9  # body bottom to underside of the mounting tabs
FLANGE_L = 32.3  # tab length, end to end
SCREW_SPACING = 27.8  # distance between the two tab screw holes
SHAFT_OFFSET = 5.5  # shaft centre to body centre, along the length

# servo horn pocket (takes the double-arm or cross horn from the SG90 bag)
HORN_HUB_R, HORN_TIP_R = 3.8, 2.2
HORN_LONG, HORN_SHORT = 15.5, 10.0  # centre to arm tip
HORN_DEPTH = 2.0

# light: the cradle takes anything 8-20 mm across, held by two zip ties
LIGHT_MAX_D = 20.0
SNOOT_ID = 16.5  # inside diameter of the optional snoot

# base plate
BASE_W, BASE_FRONT, BASE_BACK, BASE_T = 100.0, 30.0, -70.0, 3.0
FIN_T, FIN_W, FIN_H = 6.0, 50.0, 70.0  # the webcam's clip hangs on this fin
FIN_Y = -58.0  # front face of the fin, clear of the swinging light

ZIP_W, ZIP_T = 4.0, 2.0  # zip tie slot

OUT = Path(__file__).parent / "stl"


# ---------------------------------------------------------------- helpers
def box(x, y, z, center=True):
    return Manifold.cube([x, y, z], center)


def cyl(h, r, center=True):
    return Manifold.cylinder(h, r, r, 0, center)


def triangle(a, b, thick):
    """Right triangle with legs a (along X) and b (along Y), extruded thick along Z."""
    return Manifold.extrude(CrossSection([[[0, 0], [a, 0], [0, b]]]), thick)


def horn_pocket(depth=HORN_DEPTH):
    """Cross-shaped pocket that a double-arm or cross horn drops into."""
    pocket = Manifold()
    for length, angle in ((HORN_LONG, 0), (HORN_LONG, 180), (HORN_SHORT, 90), (HORN_SHORT, 270)):
        hub = cyl(depth, HORN_HUB_R + CLEAR / 2, center=False)
        a = np.radians(angle)
        tip = cyl(depth, HORN_TIP_R + CLEAR / 2, center=False).translate(
            [length * np.cos(a), length * np.sin(a), 0]
        )
        pocket += Manifold.batch_hull([hub, tip])
    return pocket


def save(m, name):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(vertices=mesh.vert_properties[:, :3], faces=mesh.tri_verts)
    OUT.mkdir(exist_ok=True)
    t.export(OUT / f"{name}.stl")
    lo, hi = t.bounds
    size = hi - lo
    print(f"{name:12s} {size[0]:5.1f} x {size[1]:5.1f} x {size[2]:5.1f} mm  watertight={t.is_watertight}")
    return t


# ---------------------------------------------------------------- parts
def base_plate():
    """Plate with a cradle for the pan servo and a fin for the webcam clip.

    The pan shaft sits at (0, 0). The servo's length runs along X.
    """
    plate = box(BASE_W, BASE_FRONT - BASE_BACK, BASE_T, center=False).translate([-BASE_W / 2, BASE_BACK, 0])

    in_l, in_w, wall = SERVO_L + CLEAR, SERVO_W + CLEAR, 2.4
    cx = -SHAFT_OFFSET  # body centre, so the shaft lands on (0, 0)
    out_l, out_w = FLANGE_L + 2, in_w + 2 * wall
    cradle = box(out_l, out_w, FLANGE_Z, center=False).translate([cx - out_l / 2, -out_w / 2, BASE_T])
    cradle -= box(in_l, in_w, FLANGE_Z + 2, center=False).translate([cx - in_l / 2, -in_w / 2, BASE_T - 1])
    for sx in (-SCREW_SPACING / 2, SCREW_SPACING / 2):  # tab screw pilot holes
        cradle -= cyl(9, 0.9, center=False).translate([cx + sx, 0, BASE_T + FLANGE_Z - 8])
    for sx in (-1, 1):  # cable slots at both ends
        cradle -= box(8, 5.5, 7, center=False).translate([cx + sx * (in_l / 2 + 2.8) - 4, -2.75, BASE_T - 0.5])

    fin = box(FIN_W, FIN_T, FIN_H, center=False).translate([-FIN_W / 2, FIN_Y - FIN_T, 0])
    for gx in (-FIN_W / 2 + 2, FIN_W / 2 - 5):  # gussets on the front face
        g = triangle(22, 30, 3).rotate([90, 0, 0]).rotate([0, 0, 90])  # thick along X, long along Y, tall along Z
        fin += g.translate([gx + 3, FIN_Y, 0])
    for zz in (FIN_H - 12, FIN_H - 28):  # spare zip tie slots
        for sx in (-15, 15):
            fin -= box(ZIP_W, FIN_T + 2, ZIP_T, center=False).translate([sx - ZIP_W / 2, FIN_Y - FIN_T - 1, zz])

    holes = Manifold()
    for x in (-BASE_W / 2 + 6, BASE_W / 2 - 6):
        for y in (BASE_BACK + 6, BASE_FRONT - 6):
            holes += cyl(10, 1.8).translate([x, y, 0])

    return plate + cradle + fin - holes


def pan_yoke():
    """Sits on the pan horn and holds the tilt servo on its side, shaft pointing +X.

    Origin = pan axis. z = 0 is the underside that sits on the horn.
    """
    t, wall_t = 4.0, 3.0
    x0, x1 = -20.0, 14.0
    y0, y1 = -24.0, 13.0
    body_y = -SHAFT_OFFSET  # tilt shaft lands on y = 0

    floor = box(x1 - x0, y1 - y0, t, center=False).translate([x0, y0, 0])
    floor -= horn_pocket().translate([0, 0, -0.01])
    floor -= cyl(10, 3.2)  # screwdriver access to the horn screw

    wall_h = SERVO_W + 12
    zc = t + wall_h / 2 - 1  # tilt servo centre height
    wall = box(wall_t, y1 - y0, wall_h, center=False).translate([x1, y0, 0])
    wall -= box(wall_t + 2, SERVO_L + CLEAR, SERVO_W + CLEAR).translate([x1 + wall_t / 2, body_y, zc])
    for sy in (-SCREW_SPACING / 2, SCREW_SPACING / 2):
        wall -= Manifold.cylinder(wall_t + 2, 0.9, 0.9, 0, True).rotate([0, 90, 0]).translate(
            [x1 + wall_t / 2, body_y + sy, zc]
        )
    for gy in (y0, y1 - 3):  # gussets, clear of the servo body
        g = triangle(10, 12, 3).rotate([90, 0, 0]).rotate([0, 0, 180])
        wall += g.translate([x1, gy, t])
    return floor + wall


def light_clamp():
    """Fixes to the tilt horn. The light lies in a U and is held by two zip ties.

    Modelled lying flat: horn pocket on the bottom face, U on top, beam along +Y.
    """
    t, wall, length = 4.0, 2.5, 34.0
    r_in = LIGHT_MAX_D / 2
    plate = box(40, 40, t, center=False).translate([-20, -20, 0])
    # long horn arms run along the beam, matching a horn fitted parallel to the servo body
    plate -= horn_pocket().rotate([0, 0, 90]).translate([0, 0, -0.01])
    plate -= cyl(10, 3.2)

    u = Manifold.cylinder(length, r_in + wall, r_in + wall, 0, True).rotate([90, 0, 0])
    u -= Manifold.cylinder(length + 2, r_in, r_in, 0, True).rotate([90, 0, 0])
    u -= box(2 * (r_in + wall) + 2, length + 2, r_in + wall + 1, center=False).translate(
        [-(r_in + wall) - 1, -length / 2 - 1, 0]
    )  # keep the lower half: a U you lay the light into
    u = u.translate([0, 0, t + r_in + wall - 1.5])
    stem = box(10, length, 2.5, center=False).translate([-5, -length / 2, t - 0.01])
    part = plate + stem + u
    for sy in (-10, 10):  # zip tie tunnels under the light
        part -= box(2 * (r_in + wall) + 4, ZIP_W, ZIP_T).translate([0, sy, t + 1.6])
    return part


def snoot():
    """Optional tube that narrows the beam. Slides over the light's head."""
    h = 40
    tube = cyl(h, SNOOT_ID / 2 + 2, center=False)
    tube -= cyl(h - 3, SNOOT_ID / 2, center=False).translate([0, 0, -0.01])
    tube -= cyl(10, 4.0).translate([0, 0, h])  # 8 mm hole in the cap
    return tube


def fit_coupon():
    """Print this first (about 10 minutes): checks the servo, horn and zip tie fits."""
    t = 4.0
    plate = box(44, 40, t, center=False).translate([-22, -20, 0])
    plate -= box(SERVO_L + CLEAR, SERVO_W + CLEAR, t + 2).translate([-5, 10, t / 2])
    for sx in (-SCREW_SPACING / 2, SCREW_SPACING / 2):
        plate -= cyl(t + 2, 0.9).translate([-5 + sx, 10, t / 2])
    plate -= horn_pocket().translate([0, -6, -0.01])
    plate -= box(ZIP_W, ZIP_T, t + 2).translate([16, 14, t / 2])
    return plate


PARTS = {
    "base_plate": base_plate,
    "pan_yoke": pan_yoke,
    "light_clamp": light_clamp,
    "snoot": snoot,
    "fit_coupon": fit_coupon,
}

if __name__ == "__main__":
    for name, make in PARTS.items():
        save(make(), name)
