# Headless: build a skirt straight from the character's own body (no AI mesh needed) -> Y-up cm OBJ with UVs.
# Waist = narrowest torso ring found automatically; hem = knee * hem_k. A-line flare, waistband, 4 mm cloth thickness.
#   blender -b -P make_skirt.py -- <body_tpose.obj Z-up> <out.obj> [style=aline|pencil] [hem_k=0.92] [ease=1.2] [flare=6]
# hem_k: hem height as a fraction of knee height (1.0 = at the knee, 0.9 = just below). flare: extra hem radius cm (A-line).
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
body_p, out_p = a[0], a[1]
kw = dict(x.split("=") for x in a[2:])
STYLE = kw.get("style", "aline"); HEM_K = float(kw.get("hem_k", 0.92)); EASE = float(kw.get("ease", 1.2))
FLARE = float(kw.get("flare", 6 if STYLE == "aline" else 1.0)); NA = 128
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=body_p, forward_axis="Y", up_axis="Z", use_split_groups=True)
body = next(o for o in sc.objects if o.type == "MESH" and "CC_Base_Body" in o.name)
P = [body.matrix_world @ v.co for v in body.data.vertices]
H = max(p.z for p in P); H0 = min(p.z for p in P); Ht = H - H0
cx = sum(p.x for p in P) / len(P); cy = sum(p.y for p in P) / len(P)


def girth_ring(z, band=0.8):
    """true radial extent per angle (follows every dip) - used only to FIND the waist height"""
    r = [0.0] * NA
    for p in P:
        if abs(p.z - z) < band and abs(p.x - cx) < 0.16 * Ht:
            dx, dy = p.x - cx, p.y - cy; k = int((math.atan2(dy, dx) % (2 * math.pi)) / (2 * math.pi) * NA) % NA
            r[k] = max(r[k], math.hypot(dx, dy))
    for _ in range(3):
        r = [max(r[i], 0.5 * (r[i - 1] + r[(i + 1) % NA])) for i in range(NA)]
    return r


def ring(z, band=0.8):
    """outline of the body slice (legs/hips/torso, no arms) at height z, at NA angles.
    Uses the SUPPORT function (furthest point along each direction) = the slice's convex hull, like cloth stretched
    over the body: no dips between the legs or bumps per muscle, so the skirt has no side waves."""
    pts = [(p.x - cx, p.y - cy) for p in P if abs(p.z - z) < band and abs(p.x - cx) < 0.16 * Ht]   # arms (T-pose) excluded
    if not pts: return [0.0] * NA
    r = []
    for i in range(NA):
        ang = 2 * math.pi * i / NA; ca, sa = math.cos(ang), math.sin(ang)
        r.append(max(0.0, max(x * ca + y * sa for x, y in pts)))
    for _ in range(4):                                               # soft round-off
        r = [(r[i - 2] + 2 * r[i - 1] + 3 * r[i] + 2 * r[(i + 1) % NA] + r[(i + 2) % NA]) / 9 for i in range(NA)]
    return r


# waist: narrowest torso girth between 0.56 and 0.68 of height
zs = [H0 + Ht * (0.56 + 0.005 * i) for i in range(25)]
girth = [(sum(girth_ring(z)), z) for z in zs]; waist_z = min(girth)[1] + 1.0
knee_z = H0 + 0.285 * Ht; hem_z = H0 + (knee_z - H0) * HEM_K
print("WAIST", round(waist_z, 1), "HEM", round(hem_z, 1), "height", round(Ht, 1))
NZ = max(20, int((waist_z - hem_z) / 0.9))
rings = []; run = [0.0] * NA; hip_seen = False
for j in range(NZ + 1):
    z = waist_z - (waist_z - hem_z) * j / NZ
    r = ring(z)
    run = [max(run[i], r[i]) for i in range(NA)]                      # a skirt never gets narrower below the hips
    t = j / NZ
    rr = []
    for i in range(NA):
        base = run[i] + 0.3 + (EASE - 0.3) * min(1.0, t * 4)        # snug waistband, ease below it
        if STYLE == "aline": base += FLARE * t ** 1.3
        else: base += FLARE * t
        rr.append(base)
    rr = [(rr[i - 1] + 2 * rr[i] + rr[(i + 1) % NA]) / 4 for i in range(NA)]
    rings.append((z, rr))
# VERTICAL smoothing: the running max jumps ring to ring (hip bones, thighs) and leaves horizontal ledges stacked like
# a building. Blur every angle's profile top-to-bottom (waist row fixed) -> one smooth slope; blur of a non-decreasing
# profile stays non-decreasing, so the skirt still never narrows below the hips.
prof = [list(rr) for _, rr in rings]
for _ in range(max(40, len(prof) * 2)):
    new = [prof[0]]
    for j in range(1, len(prof)):
        dn = prof[j + 1] if j + 1 < len(prof) else [2 * prof[j][i] - prof[j - 1][i] for i in range(NA)]
        new.append([(prof[j - 1][i] + 2 * prof[j][i] + dn[i]) / 4 for i in range(NA)])
    prof = new
raw = [rr for _, rr in rings]                      # blur may cut into the hips -> lift each column by a smooth offset
for i in range(NA):
    lift = max(0.0, max(raw[j][i] - prof[j][i] for j in range(len(prof))))
    for j in range(len(prof)): prof[j][i] += lift * min(1.0, j / (0.2 * len(prof)))
rings = [(z, prof[j]) for j, (z, _) in enumerate(rings)]
bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
grid = []
for z, rr in rings:
    row = []
    for i in range(NA):
        ang = 2 * math.pi * i / NA
        row.append(bm.verts.new((cx + rr[i] * math.cos(ang), cy + rr[i] * math.sin(ang), z)))
    grid.append(row)
circ = 2 * math.pi * sum(rings[-1][1]) / NA
for j in range(len(grid) - 1):
    for i in range(NA):
        i2 = (i + 1) % NA
        f = bm.faces.new((grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]))
        for lp in f.loops:
            k = grid[j].index(lp.vert) if lp.vert in grid[j] else grid[j + 1].index(lp.vert)
            jj = j if lp.vert in grid[j] else j + 1
            u = (k if not (i2 == 0 and k == 0 and lp.vert in (grid[j][i2], grid[j + 1][i2])) else NA) / NA
            lp[uv].uv = (u * 0.98 + 0.01, 0.01 + 0.98 * (1 - (rings[jj][0] - hem_z) / (waist_z - hem_z)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("skirt"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("skirt", me); sc.collection.objects.link(ob)
# normals must point outwards
c = Vector((cx, cy, 0)); f0 = me.polygons[0]
if (f0.center - Vector((cx, cy, f0.center.z))).dot(f0.normal) < 0:
    for p in me.polygons: p.flip()
so = ob.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.4; so.offset = 1; so.use_rim = True
bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="thick")
for p in me.polygons: p.use_smooth = True
for o in list(sc.objects):
    if o is not ob: bpy.data.objects.remove(o)
ob.select_set(True)
bpy.ops.wm.obj_export(filepath=out_p, export_selected_objects=True, export_uv=True, export_normals=True,
                      export_materials=False, forward_axis="NEGATIVE_Z", up_axis="Y")
print("WROTE", out_p, len(me.polygons), "faces", "waist_cm", round(2 * math.pi * sum(rings[0][1]) / NA, 1), "hem_cm", round(circ, 1))
