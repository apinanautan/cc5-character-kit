# Headless Blender "ball in a tube / hand in a glove" push-out. Never touches inputs.
# The body starts shrunk inward (all skin pulled in along its normals) and grows back to full size over the
# first frames; the garment is a cloth sim with the body as collider, so the growing skin pushes the cloth out
# into the body shape instead of the cloth eating into it. No gravity; stiff cloth keeps the design.
# blender -b -P inflate_push.py -- <body_tpose.obj Z-up cm> <garment.obj Y-up cm> <out.obj Y-up cm> <qc_prefix>
import bpy, bmesh, sys, time, json
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
body_p, gar_p, out_p, qc = a[:4]
SHRINK, GROW, FRAMES, DIST = 2.5, 25, 40, 0.35
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.use_gravity = False; sc.frame_start, sc.frame_end = 1, FRAMES


def parse(path, group=None):
    V, F, cur = [], [], None
    for ln in open(path, encoding="utf-8", errors="ignore"):
        if ln.startswith("v "): V.append(tuple(float(t) for t in ln.split()[1:4]))
        elif ln.startswith(("g ", "o ")): cur = ln.split(None, 1)[1].strip()
        elif ln.startswith("f ") and (group is None or (cur or "").startswith(group)):
            f = [int(t.split("/")[0]) - 1 for t in ln.split()[1:]]
            if len(set(f)) >= 3: F.append(f)
    return V, F


def mk(name, V, F):
    m = bpy.data.meshes.new(name); m.from_pydata(V, [], F); m.update()
    o = bpy.data.objects.new(name, m); sc.collection.objects.link(o); return o


bV, bF = parse(body_p, "CC_Base_Body")
body = mk("body", bV, bF)                                        # Z-up cm already
bm = bmesh.new(); bm.from_mesh(body.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(body.data); bm.free()
gV, gF = parse(gar_p)
gar = mk("garment", [(x, -z, y) for x, y, z in gV], gF)         # Y-up -> Z-up
nverts = len(gar.data.vertices)

# body animation: basis = shrunk, key "full" = real body, value 0 -> 1
body.shape_key_add(name="Basis"); full = body.shape_key_add(name="full", from_mix=False)
body.data.update()
for v, kv in zip(body.data.vertices, full.data): kv.co = v.co.copy()
for v in body.data.vertices: body.data.shape_keys.key_blocks["Basis"].data[v.index].co = v.co - v.normal * SHRINK
full.value = 0; full.keyframe_insert("value", frame=1); full.value = 1; full.keyframe_insert("value", frame=GROW)
col = body.modifiers.new("col", "COLLISION"); body.collision.thickness_outer = DIST; body.collision.cloth_friction = 0
body.collision.use_culling = False

cl = gar.modifiers.new("cloth", "CLOTH"); s = cl.settings; c = cl.collision_settings
s.quality = 6; s.mass = 0.3; s.air_damping = 5.0
s.tension_stiffness = s.compression_stiffness = 60; s.shear_stiffness = 30; s.bending_stiffness = 20
s.tension_damping = s.compression_damping = s.shear_damping = 10
c.use_collision = True; c.distance_min = DIST; c.collision_quality = 4
c.use_self_collision = True; c.self_distance_min = 0.12; c.self_friction = 0
cl.point_cache.frame_start, cl.point_cache.frame_end = 1, FRAMES

t = time.time()
for f in range(1, FRAMES + 1):
    sc.frame_set(f)
    if f % 10 == 0: print("frame", f, round(time.time() - t), "s", flush=True)
dg = bpy.context.evaluated_depsgraph_get(); ev = gar.evaluated_get(dg); me = ev.to_mesh()
P = [v.co.copy() for v in me.vertices]; ev.to_mesh_clear()
assert len(P) == nverts

# measure: cloth points inside the full body
from mathutils.bvhtree import BVHTree
body.shape_key_clear() if hasattr(body, "shape_key_clear") else None
full_tree = BVHTree.FromPolygons([Vector(v) for v in bV], bF)
def inside(pts):
    n = 0
    for p in pts[::5]:
        loc, nor, i, d = full_tree.find_nearest(p)
        if loc is not None and (p - loc).dot(nor) < 0: n += 1
    return n / len(pts[::5])
orig = [Vector((x, -z, y)) for x, y, z in gV]
moves = sorted((p - o).length for p, o in zip(P, orig))
rep = dict(inside_before=inside(orig), inside_after=inside(P), move_median_cm=moves[len(moves) // 2],
           move_p99_cm=moves[int(len(moves) * 0.99)], move_max_cm=moves[-1], sim_s=round(time.time() - t))
with open(out_p, "w") as w:
    for p in P: w.write("v %.5f %.5f %.5f\n" % (p.x, p.z, -p.y))        # Z-up -> Y-up
    for f in gF: w.write("f " + " ".join(str(i + 1) for i in f) + "\n")
json.dump(rep, open(out_p[:-4] + "_report.json", "w"), indent=1); print("PUSHED", json.dumps(rep))
