# Long straight centre-part hair, tucked behind the ears, for a CC5 head (made with ANA HairCraft "Cards").
# Run inside Blender 5.2 with the ANA HairCraft Studio add-on enabled (Blender MCP execute_blender_code, or):
#   blender --python blender\hair_center_part.py -- <body.obj> [out.blend]
# body.obj = bare CC5 body exported with cc5\probes\export_body_pose.py (A-Pose, cm, Y-up OBJ).
# Result objects: Hair_Guides (hidden curves), Hair_Cards (the hair), HairScalp (dark scalp under the hair).
# See docs/HAIR_GUIDE.md for what works / what failed and the tuning knobs.
import bpy, bmesh, math, random, os, sys
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BODY = argv[0] if argv else r"C:\Users\Apinan\Documents\CC5 Characters\docs\haircraft_test\pin_body.obj"
OUT = argv[1] if len(argv) > 1 else ""

# ---- knobs -------------------------------------------------------------
SEED = 8
N_FRONT = 2600        # strands from the part, flowing sideways then behind the ear
N_BACK = 2200         # strands on the back of the head, falling straight (no part at the back)
LENGTH = 0.45         # metres of hang below the ear
VOLUME = 0.07         # extra lift on top/front (0 = flat to the skull)
SWING_START = 0.95    # radians from the top where front hair starts going behind the ear
HAIR_COLOR = "Black"  # ANA material Cards_<color>
# ------------------------------------------------------------------------

ADDON = "bl_ext.user_default.ana_haircraft_studio"
ana = sys.modules.get(ADDON) or __import__(ADDON, fromlist=["x"])
LIB = os.path.join(os.path.dirname(ana.__file__), "assets", "CurveAsset.blend")

# body: CC5 OBJ is centimetres, Y-up
bpy.ops.wm.obj_import(filepath=BODY, forward_axis='Y', up_axis='Z')
body = bpy.context.selected_objects[0]
body.name = "hair_body"
if max(body.dimensions) > 10:
    body.scale = (0.01, 0.01, 0.01)
    bpy.ops.object.transform_apply(scale=True)
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

# head ellipsoid from the mesh (top of head minus ~10 cm = centre)
vs = [v.co for v in body.data.vertices]
top = max(v.z for v in vs)
hv = [v for v in vs if v.z > top - 0.16]
ymin, ymax = min(v.y for v in hv), max(v.y for v in hv)
C = Vector((0, (ymin + ymax) / 2, top - 0.10))
rx, ry, rz = 0.082, (ymax - ymin) / 2 * 1.04, 0.105

random.seed(SEED)
ease = lambda t: t * t * (3 - 2 * t)


def push(p, g=0.006):
    loc, nor, i, d = bvh.find_nearest(p)
    if loc is None:
        return p
    if (p - loc).dot(nor) < 0 or d < g - 0.001:
        return loc + nor * g
    return p


def surf(y, psi, side, k):  # point on head, y = front/back, psi = angle from the part down the side
    f = math.sqrt(max(0.0, 1 - (y / ry) ** 2))
    return C + Vector((side * rx * k * f * math.sin(psi), y * k, rz * k * f * math.cos(psi)))


def sph(th, ph, k):  # point on head, th = azimuth (0 front), ph = angle from top
    return C + Vector((rx * k * math.sin(ph) * math.sin(th), -ry * k * math.sin(ph) * math.cos(th), rz * k * math.cos(ph)))


def hang(pts, xs, L, NP, nA):  # straight fall behind the shoulders (not resting on them)
    last = pts[-1]; nB = NP - nA; yb = 0.13 + C.y
    for j in range(1, nB + 1):
        t = j / nB; e = ease(min(1, t * 3))
        y = last.y + (yb - last.y) * e if last.y < yb else last.y
        pts.append(push(Vector((last.x + (xs - last.x) * e, y, last.z - L * t))))


def over_ear(pts):
    for p in pts:
        r = p - C
        if abs(r.x) > 0.06 and -0.03 < r.y < 0.05 and -0.07 < r.z < 0.035:
            return True
    return False


NP, nA = 34, 16
YB = C.y + 0.05
strands = []
while len(strands) < N_FRONT:
    side = random.choice((-1, 1))
    yr = random.uniform(-0.78 * ry, 0.25 * ry)
    psi0 = random.uniform(0.02, (0.9 if yr > -0.45 * ry else 0.6) if yr < -0.3 * ry else 1.15)
    pts = []
    for i in range(nA):
        t = i / (nA - 1); psi = psi0 + (math.radians(92) - psi0) * t
        k = 1.07 + VOLUME * (1 - ease(min(1, psi / 1.3)))
        w = ease(min(1, max(0, (psi - SWING_START) / 0.6)))
        pts.append(push(surf(yr + (max(yr, YB) - yr) * w, psi, side, k)))
    hang(pts, C.x + side * random.uniform(0.02, 0.075), random.uniform(LENGTH - 0.01, LENGTH + 0.01), NP, nA)
    strands.append(pts)
nb = 0
while nb < N_BACK:
    th0 = random.uniform(math.radians(100), math.radians(260)); ph0 = random.uniform(0.05, 1.9)
    pts = []
    for i in range(nA):
        t = i / (nA - 1); ph = ph0 + (max(ph0, math.radians(118)) - ph0) * t
        pts.append(push(sph(th0, ph, 1.07 + 0.05 * (1 - ease(min(1, ph / 1.4))))))
    if over_ear(pts):
        continue
    hang(pts, max(-0.08, min(0.08, pts[-1].x)), random.uniform(LENGTH - 0.01, LENGTH + 0.01), NP, nA)
    strands.append(pts); nb += 1

flat = [c for s in strands for p in s for c in p]


def new_curves(name):
    cd = bpy.data.hair_curves.new(name)
    cd.add_curves([NP] * len(strands))
    cd.attributes['position'].data.foreach_set('vector', flat)
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    cd.surface = body
    return ob


guides = new_curves("Hair_Guides")
guides.hide_render = guides.hide_viewport = True
cards = new_curves("Hair_Cards")

# ANA HairCraft Cards node group + material (append from the add-on's own asset file)
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.node_groups = [n for n in ["Cards"] if n not in bpy.data.node_groups]
    dst.materials = [m for m in ["Cards_" + HAIR_COLOR] if m not in bpy.data.materials]
mat = bpy.data.materials["Cards_" + HAIR_COLOR]
m = cards.modifiers.new("Cards", "NODES")
m.node_group = bpy.data.node_groups["Cards"]
I = m.properties.inputs  # Blender 5.x API (the add-on's own m['Input_x']=... crashes on 5.2)
I.Input_6.value = mat    # Material
I.Input_5.value = 0.022  # Card Width
I.Input_7.value = 5      # Duplicate Amount
I.Input_8.value = 0.002  # Duplicate Radius
I.Input_3.value = 0.0    # Twist   (0 = straight)
I.Input_9.value = 0.0    # Clump
I.Input_10.value = 0.0   # Frizz   (0 = sleek, no flyaways)
I.Input_11.value = 0.0
cards.data.materials.append(mat)

# dark scalp under the hair so skin never shows between cards
kd = kdtree.KDTree(len(strands) * 8); k = 0
for s in strands:
    for p in s[0:16:2]:
        kd.insert(p, k); k += 1
kd.balance()
bm = bmesh.new(); bm.from_mesh(body.data)
keep = set(v.index for v in bm.verts if v.co.z > top - 0.25 and kd.find(v.co)[2] < 0.016)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.normal_update()
for v in bm.verts:
    v.co += v.normal * 0.002
me = bpy.data.meshes.new("HairScalp"); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
sm = bpy.data.materials.new("ScalpDark"); sm.use_nodes = True
b = sm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.012, 0.010, 0.009, 1); b.inputs["Roughness"].default_value = 0.6
me.materials.append(sm)
sp = bpy.data.objects.new("HairScalp", me); bpy.context.scene.collection.objects.link(sp)

if OUT:
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
result = {"strands": len(strands), "centre": list(C)}
print(result)
