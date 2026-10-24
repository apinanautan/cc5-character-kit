# Blender headless: fit an AI-made garment (Hunyuan GLB, T-pose) onto a CC5 body exported in T-pose.
#   blender -b --python blender/fit_garment.py -- <garment.glb> <body_tpose.obj> <out.obj> [top|bottom] [gap_cm]
# 1) garment -> CC5 space (cm, Z-up), 2) scale/move so collar, shoulders and hem sit on the body,
# 3) push every garment point that is inside or too close to the skin out to gap_cm, smoothed, 4) export OBJ + texture.
import bpy, bmesh, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index("--") + 1:]
g_path, b_path, out = a[:3]
kind = a[3] if len(a) > 3 else "top"
gap = float(a[4]) if len(a) > 4 else 0.6

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=b_path, forward_axis="Y", up_axis="Z")  # CC5 OBJ: Z-up, cm (1 unit = 1 cm)
body = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in body:
    o.select_set(True)
bpy.context.view_layer.objects.active = body[0]
if len(body) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "body"
bv = [body.matrix_world @ v.co for v in body.data.vertices]

bpy.ops.import_scene.gltf(filepath=g_path)
gar = [o for o in bpy.context.scene.objects if o.type == "MESH" and o != body][0]
gar.name = "garment"
bpy.context.view_layer.objects.active = gar
gar.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # glTF Y-up was converted to Blender Z-up
gv = [v.co.copy() for v in gar.data.vertices]


def bbox(pts):
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


bmin, bmax = bbox(bv)
H = bmax.z - bmin.z
# body landmarks (T-pose): shoulder line = height of the arms; torso = points near the middle in X
arm = [p for p in bv if abs(p.x) > (bmax.x - bmin.x) * 0.28]
shoulder_z = sum(p.z for p in arm) / len(arm)
torso = [p for p in bv if abs(p.x) < (bmax.x - bmin.x) * 0.12]
neck_z = shoulder_z + H * 0.035
hip_z = bmin.z + H * 0.47
chest = [p for p in bv if abs(p.z - (shoulder_z - H * 0.10)) < H * 0.02 and abs(p.x) < (bmax.x - bmin.x) * 0.2]
chest_w = max(p.x for p in chest) - min(p.x for p in chest)
chest_d = max(p.y for p in chest) - min(p.y for p in chest)
cx = sum(p.x for p in torso) / len(torso)
cy = sum(p.y for p in chest) / len(chest)

gmin, gmax = bbox(gv)
if kind == "top":
    # garment: top of collar ~ neck, the torso part (middle 30% of width) defines body width
    mid = [p for p in gv if abs(p.x - (gmin.x + gmax.x) / 2) < (gmax.x - gmin.x) * 0.15]
    tmin, tmax = bbox(mid)
    sx = (chest_w * 1.12) / max(tmax.x - tmin.x, 1e-6)
    sz = sx  # keep proportions; height follows width
    sy = (chest_d * 1.15) / max(tmax.y - tmin.y, 1e-6)
    top_z = gmax.z
    for v in gar.data.vertices:
        p = v.co
        v.co = Vector(((p.x - (gmin.x + gmax.x) / 2) * sx + cx,
                       (p.y - (tmin.y + tmax.y) / 2) * sy + cy,
                       (p.z - top_z) * sz + neck_z))
else:  # bottom (skirt/trousers): waistband on the natural waist, width from the waist
    waist_z = bmin.z + H * 0.60
    waist = [p for p in bv if abs(p.z - waist_z) < H * 0.01 and abs(p.x) < (bmax.x - bmin.x) * 0.2]
    ww = max(p.x for p in waist) - min(p.x for p in waist)
    band = [p for p in gv if p.z > gmax.z - (gmax.z - gmin.z) * 0.05]
    bw = max(p.x for p in band) - min(p.x for p in band)
    s = ww * 1.06 / max(bw, 1e-6)
    wcy = sum(p.y for p in waist) / len(waist)
    for v in gar.data.vertices:
        p = v.co
        v.co = Vector(((p.x - (gmin.x + gmax.x) / 2) * s + cx, (p.y - (gmin.y + gmax.y) / 2) * s + wcy,
                       (p.z - gmax.z) * s + waist_z + H * 0.01))

# push out of the skin: nearest body point + its normal; anything closer than gap goes out to gap
bm = bmesh.new()
bm.from_mesh(body.data)
bm.transform(body.matrix_world)
bvh = BVHTree.FromBMesh(bm)
disp = [Vector() for _ in gar.data.vertices]
moved = 0
crotch_z = bmin.z + H * 0.48
for i, v in enumerate(gar.data.vertices):
    if kind == "bottom" and v.co.z < crotch_z:
        continue  # a skirt hangs free below the hips: pushing it off the legs only tears it
    hit = bvh.find_nearest(v.co, 30.0)
    if hit[0] is None:
        continue
    loc, nrm, _, dist = hit
    side = (v.co - loc).dot(nrm)
    if side < gap:
        disp[i] = nrm * (gap - side)
        moved += 1
# smooth the push over neighbours so there are no dents/spikes
nbr = [set() for _ in gar.data.vertices]
for e in gar.data.edges:
    x, y = e.vertices
    nbr[x].add(y); nbr[y].add(x)
for _ in range(8):
    new = []
    for i, dv in enumerate(disp):
        if nbr[i]:
            avg = sum((disp[j] for j in nbr[i]), Vector()) / len(nbr[i])
            new.append(dv if dv.length >= avg.length else dv * 0.4 + avg * 0.6)
        else:
            new.append(dv)
    disp = new
for v, dv in zip(gar.data.vertices, disp):
    v.co += dv
print("FIT kind=%s chest_w=%.1f neck_z=%.1f moved=%d of %d" % (kind, chest_w, neck_z, moved, len(disp)))

bpy.ops.object.select_all(action="DESELECT")
gar.select_set(True)
bpy.context.view_layer.objects.active = gar
bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                      export_materials=True, path_mode="COPY", export_normals=True, export_uv=True)
print("WROTE", out)
# preview: body + garment, front and side
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
w = bpy.data.worlds.new("w"); w.color = (0.75, 0.75, 0.78); scene.world = w
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); scene.collection.objects.link(sun)
ctr = Vector(((bmin.x + bmax.x) / 2, (bmin.y + bmax.y) / 2, shoulder_z - H * 0.12))
for tag, ang in (("front", 0), ("side", 70)):
    cam = bpy.data.objects.new(tag, bpy.data.cameras.new(tag)); scene.collection.objects.link(cam)
    r = H * 1.1
    cam.location = ctr + Vector((math.sin(math.radians(ang)) * r, -math.cos(math.radians(ang)) * r, 0))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 700, 600
    scene.render.filepath = out[:-4] + "_%s.png" % tag
    bpy.ops.render.render(write_still=True)
