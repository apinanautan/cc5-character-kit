# Headless: add real buttons onto the smoothed garment where the AI sculpted button bumps.
#   blender -b -P add_buttons.py -- <low.obj Y-up, UVs> <normal.png> <buttons.json> <out.obj> <out_normal.png> <qc_prefix> [scale=1.0]
# Buttons are joined into the garment mesh (one object -> one CC5 cloth, skin-weighted together).
# CC5 re-smooths normals on import, so the button GEOMETRY is only a soft bevelled disc (no boolean holes that would
# shade as dark blobs). The rim and the 4 thread holes live in the TEXTURES: every button's UVs map onto one free
# square of the UV sheet; this script paints the button's normal map there, and writes <out>.buttons_uv.json so
# bake_fabric.py paints the button's colour picture (disc, rim, holes) into the same square.
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
low_p, nrm_p, btn_p, out_obj, out_png, qc = a[:6]
SCALE = float(a[6]) if len(a) > 6 else 1.0
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=low_p, forward_axis="NEGATIVE_Z", up_axis="Y")
gar = [o for o in sc.objects if o.type == "MESH"][0]
gar.data.transform(gar.matrix_world); gar.matrix_world = Matrix.Identity(4)   # importer puts Y-up->Z-up in the object rotation
btns = json.load(open(btn_p))
dg = bpy.context.evaluated_depsgraph_get(); tree = BVHTree.FromObject(gar, dg)

# ---- free square on the UV sheet (G x G cells of a 64 grid) for the button picture
G = 4; occ = np.zeros((64, 64), bool); uvl = gar.data.uv_layers.active.data
for poly in gar.data.polygons:
    us = [uvl[li].uv for li in poly.loop_indices]
    u0, u1 = min(u.x for u in us), max(u.x for u in us); v0, v1 = min(u.y for u in us), max(u.y for u in us)
    occ[max(0, int(v0 * 64)):min(64, int(v1 * 64) + 1), max(0, int(u0 * 64)):min(64, int(u1 * 64) + 1)] = True
cell = next(((i, j) for i in range(64 - G - 1) for j in range(64 - G - 1)
             if not occ[max(0, i - 1):i + G + 1, max(0, j - 1):j + G + 1].any()), None)
if cell is None: sys.exit("NO FREE UV SQUARE for the buttons")
CU, CV, HALF = (cell[1] + G / 2) / 64, (cell[0] + G / 2) / 64, G / 2 / 64 * 0.92
print("BUTTON UV SQUARE", cell, round(CU, 4), round(CV, 4), round(HALF, 4))


def make_button(r, t):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r * 0.97, depth=t)
    uvl_ = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:                                       # planar map: picture centre = button centre
            co = lp.vert.co; lp[uvl_].uv = (CU + co.x / r * HALF, CV + co.y / r * HALF)
    me = bpy.data.meshes.new("btn"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("btn", me); sc.collection.objects.link(ob)
    bv = ob.modifiers.new("bev", "BEVEL"); bv.width = t * 0.45; bv.segments = 4; bv.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="bev")
    for p in ob.data.polygons: p.use_smooth = True                # smooth on purpose: looks the same after CC5 import
    return ob


placed = []
for b in btns:
    x, y, z = b["pos"]; p = Vector((x, -z, y))                   # Y-up -> Blender Z-up
    nx, ny, nz = b["normal"]; nrm = Vector((nx, -nz, ny)).normalized()
    loc, n2, _, _ = tree.find_nearest(p)
    if loc is None: continue
    n2 = n2.normalized() if n2.dot(nrm) > 0 else -n2.normalized()
    r = b["radius"] * 0.95 * SCALE; t = max(0.2, r * 0.3)
    ob = make_button(r, t)
    rot = n2.to_track_quat("Z", "Y").to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(loc + n2 * (t * 0.5 + 0.03)) @ rot
    placed.append(ob)
print("BUTTONS", len(placed))

# ---- button normal map into its square (height field: raised rim, dished middle, 4 deep holes)
img = bpy.data.images.load(nrm_p); W, H = img.size
px = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
S = int(G / 64 * W); y0, x0 = int(cell[0] / 64 * H), int(cell[1] / 64 * W)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
uu = ((x0 + xx + 0.5) / W - CU) / HALF; vv = ((y0 + yy + 0.5) / H - CV) / HALF   # -1..1 = button radius
rr = np.hypot(uu, vv)


def button_height(u, v, rr):
    h = 0.25 * np.clip(1 - rr, 0, 1) ** 0.3                       # rounded edge
    h += 0.10 * np.exp(-((rr - 0.80) / 0.07) ** 2)               # raised rim
    h -= 0.06 * np.clip(1 - rr / 0.66, 0, 1)                     # dished centre
    for k in range(4):
        ang = math.pi / 4 + k * math.pi / 2; hx, hy = 0.30 * math.cos(ang), 0.30 * math.sin(ang)
        h -= 0.22 * (np.hypot(u - hx, v - hy) < 0.11)             # thread holes
    return h


hgt = button_height(uu, vv, rr)
gy, gx = np.gradient(hgt, 2 / S)
n = np.dstack([-gx * 0.6, -gy * 0.6, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
px[y0:y0 + S, x0:x0 + S, :3] = n * 0.5 + 0.5; px[y0:y0 + S, x0:x0 + S, 3] = 1
img.pixels[:] = px.ravel(); img.filepath_raw = out_png; img.file_format = "PNG"; img.save()
json.dump(dict(u=CU, v=CV, half=HALF, cell=list(cell), grid=G), open(out_obj.rsplit(".", 1)[0] + ".buttons_uv.json", "w"))

for ob in placed:
    if ob.data.uv_layers.active.name != gar.data.uv_layers.active.name: ob.data.uv_layers.active.name = gar.data.uv_layers.active.name
bpy.ops.object.select_all(action="DESELECT")
for o in placed + [gar]: o.select_set(True)
bpy.context.view_layer.objects.active = gar; bpy.ops.object.join()
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_uv=True, export_normals=True,
                      export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y")
print("WROTE", out_obj, len(gar.data.polygons), "faces")
