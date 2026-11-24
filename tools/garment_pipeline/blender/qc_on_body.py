# Headless QC: body (grey) + garment (teal) workbench renders: front / side / back / chest close-up / side close-up.
# blender -b -P qc_on_body.py -- <body_tpose.obj Z-up cm> <garment.obj Y-up cm> <out_prefix>
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; body_p, gar_p, pre = a[:3]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
def parse(path, group=None, yup=False):
    V, F, cur = [], [], None
    for ln in open(path, encoding="utf-8", errors="ignore"):
        if ln.startswith("v "):
            x, y, z = (float(t) for t in ln.split()[1:4]); V.append((x, -z, y) if yup else (x, y, z))
        elif ln.startswith(("g ", "o ")): cur = ln.split(None, 1)[1].strip()
        elif ln.startswith("f ") and (group is None or (cur or "").startswith(group)):
            f = [int(t.split("/")[0]) - 1 for t in ln.split()[1:]]
            if len(set(f)) >= 3: F.append(f)
    return V, F
def mk(name, VF, col):
    m = bpy.data.meshes.new(name); m.from_pydata(VF[0], [], VF[1]); m.update()
    for p in m.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, m); sc.collection.objects.link(o); o.color = col; return o
mk("body", parse(body_p, "CC_Base_Body"), (0.75, 0.6, 0.5, 1))
g = mk("garment", parse(gar_p, yup=True), (0.2, 0.5, 0.53, 1))
sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "OBJECT"; sh.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 900, 1000
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
bb = [g.matrix_world @ Vector(c) for c in g.bound_box]; c = sum(bb, Vector()) / 8
views = [("front", (0, -1, 0), 150, c), ("side", (1, 0, 0), 150, c), ("back", (0, 1, 0), 150, c),
         ("close_chest", (0, -1, 0), 60, c + Vector((0, 0, 12))), ("close_side", (1, -0.3, 0), 60, c + Vector((8, 0, 5)))]
for tag, d, dist, aim in views:
    cam.location = aim + Vector(d).normalized() * dist
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = pre + tag + ".png"; bpy.ops.render.render(write_still=True)
