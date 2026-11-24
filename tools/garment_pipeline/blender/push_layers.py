# Headless: make sure the garment clears the body AND the clothes worn under it (pants waistband etc.) by >= gap cm.
# Vertices closer than gap are moved out along the under-layer normal; the move is spread to neighbours so no dents/spikes.
#   blender -b -P push_layers.py -- <garment.obj Y-up> <body_tpose.obj Z-up> <out.obj> <gap_cm> <group,group,...>
import bpy, sys, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
g_p, b_p, out_p, GAP, groups = a[0], a[1], a[2], float(a[3]), a[4].split(",")
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=g_p, forward_axis="NEGATIVE_Z", up_axis="Y")
gar = [o for o in sc.objects if o.type == "MESH"][0]; gar.data.transform(gar.matrix_world); gar.matrix_world = Matrix.Identity(4)
bpy.ops.wm.obj_import(filepath=b_p, forward_axis="Y", up_axis="Z", use_split_groups=True)
under = [o for o in sc.objects if o.type == "MESH" and o is not gar and any(g in o.name for g in groups)]


def outer_shell(o):
    """keep only the outward-facing faces of a cloth (thick / double-sided clothes have an inner shell whose normal
    points at the body; pushing along it would pull our garment INTO the cloth)"""
    o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    b2 = bmesh.new(); b2.from_mesh(o.data); b2.faces.ensure_lookup_table()
    ctr = sum((v.co for v in b2.verts), Vector()) / len(b2.verts)
    inner = [f for f in b2.faces if f.normal.dot(f.calc_center_median() - Vector((ctr.x, ctr.y, f.calc_center_median().z))) < 0]
    bmesh.ops.delete(b2, geom=inner, context="FACES")
    b2.to_mesh(o.data); b2.free()


for o in under:
    if "CC_Base" not in o.name: outer_shell(o)          # library clothes from a CC5 export (skirt, pants...)
for extra in a[5:]:                                     # more under-layers made by us (Y-up OBJ, e.g. the new skirt)
    before = set(sc.objects); bpy.ops.wm.obj_import(filepath=extra, forward_axis="NEGATIVE_Z", up_axis="Y")
    for o in [o for o in sc.objects if o not in before]:
        outer_shell(o); under.append(o)
print("UNDER", [o.name for o in under])
# one tree PER layer: our garment usually sits between the body and the other cloth, nearer the body, so a single
# combined "nearest surface" would only ever see the body and never push the garment out over the cloth.
trees = []
for o in under:
    bm = bmesh.new(); m = o.data.copy(); m.transform(o.matrix_world); bm.from_mesh(m)
    trees.append((BVHTree.FromBMesh(bm), "CC_Base" in o.name)); bm.free()
me = gar.data; n = len(me.vertices)
mv = [Vector() for _ in range(n)]; hit = 0; worst = 99
for i, v in enumerate(me.vertices):
    best = Vector()
    for tree, is_body in trees:
        loc, nrm, _, d = tree.find_nearest(v.co, 6.0)
        if loc is None: continue
        s = (v.co - loc).dot(nrm)
        if not is_body and abs(s) < 0.7 * d: continue    # nearest point is a cloth EDGE (e.g. above the waistband): ignore
        worst = min(worst, s)
        if s < GAP and (GAP - s) > best.length: best = nrm * (GAP - s)
    if best.length: mv[i] = best; hit += 1
# keep the cloth's own thickness: the AI garment has an inner and an outer skin. Pushing each vertex to "gap" on its own
# would land BOTH skins on the same surface (they overlap and the texture breaks). So every vertex takes the largest move
# of any garment vertex within THICK cm -> inner + outer skin move together as one slab.
from mathutils.kdtree import KDTree
THICK = 1.2
kd = KDTree(n)
for i, v in enumerate(me.vertices): kd.insert(v.co, i)
kd.balance()
mv0 = list(mv)
for i, v in enumerate(me.vertices):
    for _, j, _ in kd.find_range(v.co, THICK):
        if mv0[j].length > mv[i].length: mv[i] = mv0[j]
# spread: 4 rounds of max-blend with neighbours so the patch is pushed as a smooth bump
nb = [[] for _ in range(n)]
for e in me.edges: i, j = e.vertices; nb[i].append(j); nb[j].append(i)
for _ in range(4):
    new = list(mv)
    for i in range(n):
        if nb[i]:
            avg = sum((mv[j] for j in nb[i]), Vector()) / len(nb[i])
            if avg.length * 0.7 > new[i].length: new[i] = avg * 0.7
    mv = new
# small separate pieces (buttons) must move as one rigid piece, never bend: use their largest push for every vertex
seen = [False] * n; rigid = 0
for s0 in range(n):
    if seen[s0]: continue
    comp, stack = [], [s0]; seen[s0] = True
    while stack:
        i = stack.pop(); comp.append(i)
        for j in nb[i]:
            if not seen[j]: seen[j] = True; stack.append(j)
    if len(comp) < 0.05 * n:
        big = max((mv[i] for i in comp), key=lambda x: x.length)
        for i in comp: mv[i] = big
        rigid += 1
print("RIGID PIECES", rigid)
for i, v in enumerate(me.vertices): v.co += mv[i]
print("PUSHED", hit, "verts under gap; worst signed gap before", round(worst, 3))
for o in list(sc.objects):
    if o is not gar: bpy.data.objects.remove(o)
gar.select_set(True); bpy.context.view_layer.objects.active = gar
bpy.ops.wm.obj_export(filepath=out_p, export_selected_objects=True, export_uv=True, export_normals=True,
                      export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y")
print("WROTE", out_p)
