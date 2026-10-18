# Blender (headless): fix one garment poking through another, deterministically.
#   blender -b --python blender_layer_fix.py -- <char.fbx> <outer mesh> <inner mesh> <out.fbx> [offset_m]
# Every vertex of OUTER that is inside INNER (or closer than offset to its surface) is moved to the
# nearest INNER surface point + normal*offset; the move is blended into nearby vertices so there is no crease.
#   shirt over trousers : outer=shirt, inner=trousers
#   shirt tucked in     : outer=trousers, inner=shirt
# Works in the rest shape (armature off), keeps skeleton + skin weights, exports OUTER (+armature) for CC5 LoadClotheFromFbx.
import bpy, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
fbx, outer_name, inner_name, out = args[:4]
offset = float(args[4]) if len(args) > 4 else 0.004
reach = 0.06  # only vertices within 6 cm of INNER are considered

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]


def find(name):
    hit = [o for o in meshes if o.name == name] or [o for o in meshes if name.lower() in o.name.lower()]
    if not hit:
        raise SystemExit("NO MESH %r in %r" % (name, [o.name for o in meshes]))
    return hit[0]


outer, inner = find(outer_name), find(inner_name)
arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
bpy.context.view_layer.update()  # measure in the CURRENT pose (what CC5 shows), apply the push to the rest shape

# INNER as a world-space BVH
dg = bpy.context.evaluated_depsgraph_get()
ie = inner.evaluated_get(dg)
imesh = ie.to_mesh()
mw = inner.matrix_world
verts = [mw @ v.co for v in imesh.vertices]
polys = [list(p.vertices) for p in imesh.polygons]
bvh = BVHTree.FromPolygons(verts, polys)
ie.to_mesh_clear()

ow, owi = outer.matrix_world, outer.matrix_world.inverted()
me = outer.data
oe = outer.evaluated_get(dg)
omesh = oe.to_mesh()
pos = [ow @ v.co for v in omesh.vertices]  # posed positions, same vertex order as me
rest = [ow @ v.co for v in me.vertices]
oe.to_mesh_clear()
disp = [Vector() for _ in pos]
moved = 0
# "outward" = horizontally away from the inner garment's centre line (garments wrap around the body).
cx = sum(v.x for v in verts) / len(verts)
cy = sum(v.y for v in verts) / len(verts)
zlo, zhi = min(v.z for v in verts), max(v.z for v in verts)


def last_hit(p, d):
    """Farthest INNER surface along ray p->d within reach (handles double-sided waistbands)."""
    far, start, travelled = None, p.copy(), 0.0
    while travelled < reach:
        loc, nrm, _, dist = bvh.ray_cast(start, d, reach - travelled)
        if loc is None:
            break
        far = loc
        travelled += dist + 1e-4
        start = loc + d * 1e-4
    return far


for i, p in enumerate(pos):
    if not (zlo - 0.01 <= p.z <= zhi + 0.01):
        continue
    d = Vector((p.x - cx, p.y - cy, 0.0))
    if d.length < 1e-6:
        continue
    d.normalize()
    hit = last_hit(p, d)
    if hit is None:
        # no INNER outside this point; still keep a gap if INNER is just barely outside/at it
        continue
    disp[i] = (hit + d * offset) - p
    moved += 1

# blend: spread the push to neighbours (keeps the hem smooth), never pull a pushed vertex back in
nbr = [[] for _ in pos]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
for _ in range(6):
    new = []
    for i, d in enumerate(disp):
        if nbr[i]:
            avg = sum((disp[j] for j in nbr[i]), Vector()) / len(nbr[i])
            new.append(d if d.length >= avg.length else d * 0.5 + avg * 0.5)
        else:
            new.append(d)
    disp = new
for v, r, d in zip(me.vertices, rest, disp):
    if d.length > 0:
        v.co = owi @ (r + d)  # hips barely rotate between bind and current pose, so the world push carries over
me.update()
print("MOVED", moved, "of", len(pos), "offset", offset)

bpy.ops.object.select_all(action="DESELECT")
outer.select_set(True)
if arm:
    arm.select_set(True)
    arm.data.pose_position = "REST"  # export the bind shape; CC5 applies its own pose (else the pose is applied twice = bloated)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         path_mode="COPY", embed_textures=False)
print("EXPORTED", out)
