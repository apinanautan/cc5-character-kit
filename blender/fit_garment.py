# Blender headless: fit an AI-made garment (Hunyuan GLB) onto a CC5 body exported in T-pose.
#   blender -b --python blender/fit_garment.py -- <garment.glb> <body_tpose.obj> <out.obj> [top|bottom] [gap_cm]
# top: the garment is split into torso + left/right sleeve at its armpits; each part is placed on the matching body
#      part (torso on the chest, sleeves along the arms) and then wrapped snugly onto ONLY that part's skin, so sleeves
#      sit on the arms (CC5 then gives them arm weights) instead of floating next to the ribs.
# bottom: waistband on the natural waist, wrapped onto the hips; below the hips it hangs free.
# Writes <out>.obj (+ texture, Y-up for CC5) and <out>_front.png / _side.png previews (garment on the body).
import bpy, bmesh, math, os, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
g_path, b_path, out = a[:3]
kind = a[3] if len(a) > 3 else "top"
gap = float(a[4]) if len(a) > 4 else (1.5 if kind == "top" else 0.8)  # cm between skin and cloth (CC5 shows skin through anything closer)
LOOSE = 2.5                                     # cm of the AI garment's own looseness that is kept (folds)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=b_path, forward_axis="Y", up_axis="Z")  # CC5 OBJ: Z-up, cm
body_objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in body_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = body_objs[0]
if len(body_objs) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
bv = [body.matrix_world @ v.co for v in body.data.vertices]

bpy.ops.import_scene.gltf(filepath=g_path)
gar = [o for o in bpy.context.scene.objects if o.type == "MESH" and o != body][0]
bpy.ops.object.select_all(action="DESELECT")
gar.select_set(True)
bpy.context.view_layer.objects.active = gar
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# AI meshes come cut into pieces along their texture seams: weld them (UVs stay per corner) so moves spread smoothly
gbm = bmesh.new(); gbm.from_mesh(gar.data)
n0 = len(gbm.verts)
bmesh.ops.remove_doubles(gbm, verts=gbm.verts, dist=0.0005)
gbm.to_mesh(gar.data); gbm.free(); gar.data.update()
print("WELD %d -> %d verts" % (n0, len(gar.data.vertices)))
G = gar.data.vertices


def bbox(pts):
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))


bmin, bmax = bbox(bv)
H = bmax.z - bmin.z
cx = (bmin.x + bmax.x) / 2
# ---- body landmarks (T-pose) ----
arm_pts = [p for p in bv if abs(p.x - cx) > H * 0.25]                 # clearly arm (beyond the torso)
shoulder_z = sum(p.z for p in arm_pts) / len(arm_pts)                # arm centre height
under = [p for p in bv if abs(p.z - (shoulder_z - H * 0.07)) < H * 0.01]   # slice under the armpits: torso only
armpit_x = max(abs(p.x - cx) for p in under)                          # torso half-width at the armpit
neck = [p for p in bv if abs(p.x - cx) < H * 0.05 and shoulder_z + H * 0.02 < p.z < shoulder_z + H * 0.07]
neck_z = min(p.z for p in neck) if neck else shoulder_z + H * 0.04
chest = [p for p in bv if abs(p.z - (shoulder_z - H * 0.09)) < H * 0.01 and abs(p.x - cx) < armpit_x]
cy = (min(p.y for p in chest) + max(p.y for p in chest)) / 2
torso_d = max(p.y for p in chest) - min(p.y for p in chest)


def region_bvh(pred):
    """BVH of the body faces whose vertices all satisfy pred (torso only / one arm only)."""
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.transform(body.matrix_world)
    kill = [f for f in bm.faces if not all(pred(v.co) for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context="FACES_ONLY")
    return BVHTree.FromBMesh(bm)


def wrap(idx, bvh, keep=LOOSE):
    """Pull the given garment vertices onto the skin of one body part: gap + a little of their own looseness."""
    disp = {}
    for i in idx:
        p = G[i].co
        hit = bvh.find_nearest(p, 40.0)
        if hit[0] is None:
            continue
        loc, nrm, _, dist = hit
        side = (p - loc).dot(nrm)
        target = loc + nrm * (gap + max(0.0, min(side - gap, keep)))
        disp[i] = target - p
    return disp


if kind == "top":
    gv = [v.co for v in G]
    gmin, gmax = bbox(gv)
    gcx = (gmin.x + gmax.x) / 2
    # garment armpit: going out from the centre, where the lowest cloth point jumps up from the hem to the sleeve
    bins = {}
    for p in gv:
        b = int(abs(p.x - gcx) / ((gmax.x - gmin.x) / 80))
        bins[b] = min(bins.get(b, 1e9), p.z)
    hem = bins[0]
    g_armpit = next(((b + 1) * (gmax.x - gmin.x) / 80 for b in sorted(bins) if bins[b] > hem + (gmax.z - gmin.z) * 0.45),
                    (gmax.x - gmin.x) * 0.25)
    # one scale for the whole garment from the torso width; then sleeves are moved onto the arm line
    s = (armpit_x * 1.15) / g_armpit
    gtop = gmax.z
    gmid_y = (gmin.y + gmax.y) / 2
    # height: hem of a blouse at the hips (AI images often come out cropped/short)
    hem_z = bmin.z + H * float(os.environ.get("HEM", "0.53"))
    sz = max(s, (neck_z - hem_z) / max(gtop - hem, 1e-6))
    sy = max(s, torso_d * 1.25 / max(gmax.y - gmin.y, 1e-6))
    sleeve = []
    for i, v in enumerate(G):
        p = v.co.copy()
        if abs(p.x - gcx) > g_armpit * 1.02:
            sleeve.append(i)
        v.co = Vector(((p.x - gcx) * s + cx, (p.y - gmid_y) * sy + cy, (p.z - gtop) * sz + neck_z + H * 0.012))
    # torso depth: fit front/back to the chest
    tor = [i for i in range(len(G)) if i not in set(sleeve)]
    # sleeves: put their centre line on the arm centre line (height), keep length
    for side in (1, -1):
        ids = [i for i in sleeve if (G[i].co.x - cx) * side > 0]
        if not ids:
            continue
        zc = sum(G[i].co.z for i in ids) / len(ids)
        yc = sum(G[i].co.y for i in ids) / len(ids)
        arm_side = [p for p in arm_pts if (p.x - cx) * side > 0]
        az = sum(p.z for p in arm_side) / len(arm_side)
        ay = sum(p.y for p in arm_side) / len(arm_side)
        for i in ids:  # full move at the cuff, none at the armpit seam: the shoulder stays closed
            t = min(1.0, max(0.0, (abs(G[i].co.x - cx) - armpit_x * 1.15) / (H * 0.06)))
            G[i].co.z += (az - zc) * t
            G[i].co.y += (ay - yc) * t
    torso_bvh = region_bvh(lambda c: abs(c.x - cx) < armpit_x * 1.15 and c.z > bmin.z + H * 0.35)
    arm_bvh = region_bvh(lambda c: abs(c.x - cx) > armpit_x * 0.85)
    disp = {}  # placed by parts above; only pushed out of the skin below
else:
    gv = [v.co for v in G]
    gmin, gmax = bbox(gv)
    waist_z = bmin.z + H * 0.60
    waist = [p for p in bv if abs(p.z - waist_z) < H * 0.01 and abs(p.x - cx) < armpit_x]
    ww = max(p.x for p in waist) - min(p.x for p in waist)
    band = [p for p in gv if p.z > gmax.z - (gmax.z - gmin.z) * 0.05]
    s = ww * 1.06 / max(max(p.x for p in band) - min(p.x for p in band), 1e-6)
    wcy = sum(p.y for p in waist) / len(waist)
    for v in G:
        p = v.co
        v.co = Vector(((p.x - (gmin.x + gmax.x) / 2) * s + cx, (p.y - (gmin.y + gmax.y) / 2) * s + wcy,
                       (p.z - gmax.z) * s + waist_z + H * 0.01))
    hips_bvh = region_bvh(lambda c: bmin.z + H * 0.47 < c.z < bmin.z + H * 0.66 and abs(c.x - cx) < armpit_x * 1.3)
    disp = {}  # placed above; pushed out of the skin below (pulling in tears the AI shell)

# push out of the skin with a smooth field (never pull cloth in: that tears the AI shell), a few rounds
bm0 = bmesh.new(); bm0.from_mesh(body.data); bm0.transform(body.matrix_world)
skin = BVHTree.FromBMesh(bm0)
nb = [set() for _ in G]
for e in gar.data.edges:
    x, y = e.vertices
    nb[x].add(y); nb[y].add(x)
for rnd in range(4):
    need = [Vector() for _ in G]
    hits = 0
    for i, v in enumerate(G):
        h = skin.find_nearest(v.co, 15.0)
        if h[0] is None:
            continue
        side = (v.co - h[0]).dot(h[1])
        if side < gap:
            need[i] = h[1] * (gap - side)
            hits += 1
    for _ in range(12):  # spread, keeping the biggest push where it is needed
        need = [n if n.length >= (sum((need[j] for j in nb[i]), Vector()) / len(nb[i])).length else
                n * 0.3 + (sum((need[j] for j in nb[i]), Vector()) / len(nb[i])) * 0.7 if nb[i] else n
                for i, n in enumerate(need)]
    for v, n in zip(G, need):
        v.co += n
    print("PUSH round %d: %d points inside" % (rnd, hits))
    if hits == 0:
        break
# spread the moves to neighbours (no seams where a part ends, no spikes)
nbr = [set() for _ in G]
for e in gar.data.edges:
    x, y = e.vertices
    nbr[x].add(y); nbr[y].add(x)
D = [disp.get(i, Vector()) for i in range(len(G))]
# smooth the whole move field: the AI mesh is a thick shell (inner + outer skin of the cloth); moving every point on its
# own squashes both layers together (shards). A smooth field moves nearby points together and keeps the thickness.
for _ in range(int(os.environ.get("SMOOTH", "25"))):
    D = [(D[i] * 0.5 + (sum((D[j] for j in nbr[i]), Vector()) / len(nbr[i])) * 0.5) if nbr[i] else D[i]
         for i in range(len(G))]
for v, dv in zip(G, D):
    v.co += dv
# final pass: nothing inside the skin anywhere
bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(body.matrix_world)
all_bvh = BVHTree.FromBMesh(bm)
inside = 0
for v in G:
    hit = all_bvh.find_nearest(v.co, 10.0)
    if hit[0] is not None and (v.co - hit[0]).dot(hit[1]) < 0:
        inside += 1  # report only
print("FIT kind=%s armpit_x=%.1f shoulder_z=%.1f neck_z=%.1f wrapped=%d inside_fixed=%d of %d" % (
    kind, armpit_x, shoulder_z, neck_z, len(disp), inside, len(G)))

for img in bpy.data.images:  # textures are packed inside the GLB: write them out so the OBJ/.mtl can point at them
    if img.packed_file or not os.path.exists(bpy.path.abspath(img.filepath or "")):
        try:
            img.filepath_raw = os.path.join(os.path.dirname(out), "tex_" + bpy.path.clean_name(img.name) + ".png")
            img.file_format = "PNG"
            img.save()
            print("TEX", img.filepath_raw)
        except Exception as e:
            print("TEX fail", img.name, e)
bpy.ops.object.select_all(action="DESELECT")
gar.select_set(True)
bpy.context.view_layer.objects.active = gar
bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                      export_materials=True, path_mode="COPY", export_normals=True, export_uv=True)
print("WROTE", out)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
w = bpy.data.worlds.new("w"); w.color = (0.75, 0.75, 0.78); scene.world = w
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); scene.collection.objects.link(sun)
ctr = Vector((cx, cy, shoulder_z - H * 0.12 if kind == "top" else bmin.z + H * 0.45))
for tag, ang in (("front", 0), ("side", 70)):
    cam = bpy.data.objects.new(tag, bpy.data.cameras.new(tag)); scene.collection.objects.link(cam)
    r = H * 1.1
    cam.location = ctr + Vector((math.sin(math.radians(ang)) * r, -math.cos(math.radians(ang)) * r, 0))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 700, 600
    scene.render.filepath = out[:-4] + "_%s.png" % tag
    bpy.ops.render.render(write_still=True)
