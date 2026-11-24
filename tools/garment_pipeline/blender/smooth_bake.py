# Headless: make the garment SMOOTH and keep seams/buttons/collar edges as a NORMAL MAP (bump) instead of geometry.
#   blender -b -P smooth_bake.py -- <detail.obj Y-up cm> <out_low.obj> <out_normal.png> <qc_prefix> [smooth_iters] [high_smooth] [tex]
# low  = detail mesh smoothed strongly (shape and silhouette kept, crinkles gone), gets UVs
# high = detail mesh with a light smooth (removes tiny noise, keeps seams), baked onto low as a tangent normal map
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
src, out_obj, out_png, qc = a[:4]
ITERS = int(a[4]) if len(a) > 4 else 12
HIGH_SMOOTH = int(a[5]) if len(a) > 5 else 2
TEX = int(a[6]) if len(a) > 6 else 2048
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene


def parse(path):
    V, F = [], []
    for ln in open(path, encoding="utf-8", errors="ignore"):
        if ln.startswith("v "): x, y, z = (float(t) for t in ln.split()[1:4]); V.append((x, -z, y))   # Y-up -> Z-up
        elif ln.startswith("f "):
            f = [int(t.split("/")[0]) - 1 for t in ln.split()[1:]]
            if len(set(f)) >= 3: F.append(f)
    return V, F


def mk(name, VF):
    m = bpy.data.meshes.new(name); m.from_pydata(VF[0], [], VF[1]); m.update()
    for p in m.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, m); sc.collection.objects.link(o); return o


def select_only(*objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def apply_smooth(o, iters, factor):
    if iters <= 0: return
    select_only(o)
    m = o.modifiers.new("cs", "CORRECTIVE_SMOOTH")          # smooths crinkles but keeps the overall volume/shape
    m.iterations = iters; m.factor = factor; m.smooth_type = "LENGTH_WEIGHTED"; m.use_only_smooth = True
    m.rest_source = "ORCO"; m.scale = 1.0
    m2 = o.modifiers.new("lap", "LAPLACIANSMOOTH"); m2.iterations = max(1, iters // 3); m2.lambda_factor = 0.6
    m2.use_volume_preserve = True; m2.use_normalized = True
    for mod in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)


VF = parse(src)
high = mk("high", VF); low = mk("low", VF)
apply_smooth(high, HIGH_SMOOTH, 0.5)
apply_smooth(low, ITERS, 0.8)
moves = sorted((h.co - l.co).length for h, l in zip(high.data.vertices, low.data.vertices))
print("SMOOTH move median %.3f p99 %.3f max %.3f cm" % (moves[len(moves) // 2], moves[int(len(moves) * .99)], moves[-1]))

# UVs on low (smart project = automatic islands)
select_only(low); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0, scale_to_bounds=True)
bpy.ops.object.mode_set(mode="OBJECT")

# bake high -> low normal map
img = bpy.data.images.new("garment_normal", TEX, TEX, alpha=False, float_buffer=False); img.colorspace_settings.name = "Non-Color"
mat = bpy.data.materials.new("garment"); mat.use_nodes = True; low.data.materials.append(mat)
nt = mat.node_tree; tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; nt.nodes.active = tex
high.data.materials.append(bpy.data.materials.new("hi"))
sc.render.engine = "CYCLES"; sc.cycles.samples = 1
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "CUDA"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = "GPU"
except Exception as e: print("cpu bake", e)
b = sc.render.bake; b.use_selected_to_active = True; b.cage_extrusion = float(a[7]) if len(a) > 7 else 0.3; b.max_ray_distance = float(a[8]) if len(a) > 8 else 0.8
b.margin = 8; b.normal_space = "TANGENT"
select_only(high, low, active=low)
bpy.ops.object.bake(type="NORMAL")
img.filepath_raw = out_png; img.file_format = "PNG"; img.save()
print("BAKED", out_png)

# export low with UVs (Blender Z-up -> OBJ Y-up)
select_only(low); bpy.data.objects.remove(high)
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_uv=True, export_normals=True,
                      export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y", apply_modifiers=True)
print("WROTE", out_obj)

# QC: EEVEE with the normal map, chest close-up + full front
links = nt.links; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
nm = nt.nodes.new("ShaderNodeNormalMap"); links.new(tex.outputs["Color"], nm.inputs["Color"]); links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.53, 1); bsdf.inputs["Roughness"].default_value = 0.7
try: sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError: sc.render.engine = "BLENDER_EEVEE"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
for rot, en in (((0.9, 0, 0.6), 3.0), ((1.1, 0, -2.2), 1.5)):
    s = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); s.data.energy = en; s.rotation_euler = rot; sc.collection.objects.link(s)
sc.render.resolution_x, sc.render.resolution_y = 1000, 1000
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
bb = [low.matrix_world @ Vector(c) for c in low.bound_box]; c = sum(bb, Vector()) / 8
for tag, dist, aim in (("front", 120, c), ("close", 45, c + Vector((0, 0, 12)))):
    cam.location = aim + Vector((0, -1, 0.15)).normalized() * dist
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = qc + tag + ".png"; bpy.ops.render.render(write_still=True)
