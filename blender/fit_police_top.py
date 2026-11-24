# Blender (headless, CC5 closed): place an AI-made SHIRT (Hunyuan GLB: Y-up metres) on a CC body in T-pose.
#   blender -b --python blender\fit_ai_bottom.py -- <model.glb> <body_tpose.obj> <out.obj> <out_tex.png> <preview.png>
#     [top=0.61] [bottom=0.26]   (waist / hem height as a fraction of body height)
# Scaled so its waist sits at the body's waist and its hem at the hem line, widened if it would be tighter than the
# hips, centred on the hips; seams welded; any cloth inside the body pushed out (as a smooth field). Output OBJ is
# Y-up for CC5 LoadAccessoryWithTransferSkinWeight, with the GLB's own colour texture.
import math, sys
import bmesh, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
glb, body_path, out_obj, out_tex, out_png = a[:5]
opt = dict(x.split("=") for x in a[5:] if "=" in x)
TOP, BOTTOM = float(opt.get("top", 0.835)), float(opt.get("bottom", 0.545))  # shoulder line .. shirt hem
MIRROR = opt.get("mirror", "0") == "1"   # the AI only saw the front: rebuild the back as a mirror of the front
GAP = 0.4
PUSH = opt.get("push", "1") == "1"       # push=0: only place it; CC5 Calculate Collision does the rest

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=body_path, forward_axis="Y", up_axis="Z")
body = bpy.context.selected_objects[0]
bv = [v.co.copy() for v in body.data.vertices]
z0, z1 = min(v.z for v in bv), max(v.z for v in bv)
H = z1 - z0
zw, zh = z0 + H * TOP, z0 + H * BOTTOM
hips = [v for v in bv if abs(v.z - (z0 + H * 0.70)) < 1.0 and abs(v.x) < H * 0.13]  # chest (arms excluded)
hx0, hx1 = min(v.x for v in hips), max(v.x for v in hips)
hy0, hy1 = min(v.y for v in hips), max(v.y for v in hips)

bpy.ops.import_scene.gltf(filepath=glb)
g = [o for o in bpy.context.selected_objects if o.type == "MESH"][0]
bpy.ops.object.select_all(action="DESELECT"); g.select_set(True); bpy.context.view_layer.objects.active = g
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = g.data
# weld the AI shell's split seams
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bm.to_mesh(me); bm.free()
if MIRROR:  # GLB front faces -Y here (Blender's glTF import): keep y < centre, mirror it to the back
    yc = (min(v.co.y for v in me.vertices) + max(v.co.y for v in me.vertices)) / 2
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, yc, 0),
                           plane_no=(0, 1, 0), clear_outer=True)
    bm.to_mesh(me); bm.free()
    mm = g.modifiers.new("mirror", "MIRROR"); mm.use_axis = (False, True, False);
    mm.use_clip = True; mm.merge_threshold = 0.002
    e = bpy.data.objects.new("c", None); e.location = (0, yc, 0); bpy.context.collection.objects.link(e)
    mm.mirror_object = e
    bpy.ops.object.modifier_apply(modifier="mirror")
gv = [v.co for v in me.vertices]
gx0, gx1 = min(v.x for v in gv), max(v.x for v in gv)
gy0, gy1 = min(v.y for v in gv), max(v.y for v in gv)
gz0, gz1 = min(v.z for v in gv), max(v.z for v in gv)
s = (zw - zh) / (gz1 - gz0)
sx = s                                              # sleeves set the width: keep proportions
if 'sleeve' in opt:  # sleeve=0.92: stretch the width so the sleeve ends at that fraction of the body's arm span (wrist)
    sx = max(sx, max(abs(v.x) for v in bv) * float(opt['sleeve']) / max(abs(gx0), abs(gx1)))
sy = max(s, (hy1 - hy0) * 1.35 / (gy1 - gy0))
GROW = float(opt.get("grow", 1.0))       # roomier around the chest (x, y) without making it longer
sx, sy = sx * GROW, sy * GROW
SLEEVE_ONLY = "sleeveonly" in opt
if SLEEVE_ONLY:
    gh = max(abs(gx0 - (gx0 + gx1) / 2), abs(gx1 - (gx0 + gx1) / 2))
    xs = float(opt.get("shoulder", 0.34)) * gh
    sxt = s * float(opt.get("torso", 1.0))
    reach = max(abs(v.x) for v in bv) * float(opt.get("sleeveonly", 0.9))
    sxs = (reach - xs * sxt) / (gh - xs)
    print("SLEEVEONLY torso x%.1f sleeve x%.1f" % (sxt, sxs))
cx, cy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
gcx, gcy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
for v in me.vertices:
    dxg = v.co.x - gcx
    if SLEEVE_ONLY:   # torso keeps its natural width; only the part beyond the shoulder is stretched (sleeves reach the wrist)
        a = abs(dxg)
        nx = (a * sxt if a <= xs else xs * sxt + (a - xs) * sxs)
        dxg = math.copysign(nx, dxg)
    else:
        dxg *= sx
    v.co = Vector((cx + dxg, cy + (v.co.y - gcy) * sy, zh + (v.co.z - gz0) * s))
me.update()

# T-pose: lift / lower the whole shirt so the sleeves' centre line sits on the arms' centre line
gv = [v.co for v in me.vertices]
reach = max(abs(v.x - cx) for v in gv)
sleeve = [v for v in gv if abs(v.x - cx) > reach * 0.75]
arm = [v for v in bv if reach * 0.75 < abs(v.x - cx) < reach * 1.05]
if sleeve and arm:
    dz = sum(v.z for v in arm) / len(arm) - sum(v.z for v in sleeve) / len(sleeve)
    dy = sum(v.y for v in arm) / len(arm) - sum(v.y for v in sleeve) / len(sleeve)
    for v in me.vertices:
        v.co.z += dz
        v.co.y += dy * 0.5                # arms sit a little behind the chest line: meet halfway
    me.update()
    print("SLEEVES moved dz=%.1f dy=%.1f" % (dz, dy))

# apose=<degrees>: swing the sleeves down about the shoulder joint (CC5 A-pose arms hang ~45 deg), so the garment can be
# skinned in A-pose (T-pose skinning leaves flaps of cloth at the armpits when the arms come down).
if "apose" in opt:
    ang = math.radians(float(opt["apose"]))
    brch = max(abs(v.x - cx) for v in bv)
    px = brch * float(opt.get("pivot", 0.24))
    pz = (sum(v.z for v in arm) / len(arm)) if (sleeve and arm) else (zw - 8)
    for v in me.vertices:
        dx = abs(v.co.x - cx) - px
        if dx <= 0:
            continue
        w = min(1.0, dx / 7.0); a = ang * w
        sgn = 1 if v.co.x > cx else -1
        dz = v.co.z - pz
        nx = dx * math.cos(a) + dz * math.sin(a)
        nz = -dx * math.sin(a) + dz * math.cos(a)
        v.co.x = cx + sgn * (px + nx); v.co.z = pz + nz
    me.update(); print("APOSE sleeves %.0f deg about x=%.1f z=%.1f" % (math.degrees(ang), px, pz))

# tuck=<fraction of body height>: below that line the shirt is pulled in to sit just outside the skin, so the trousers
# (which sit over it) hide the hem = shirt tucked in. Use a lower bottom= (hem) with it, e.g. bottom=0.50 tuck=0.575.
if "tuck" in opt:
    zt = z0 + H * float(opt["tuck"])
    LIM = float(opt.get("tuckfit", 1.03))
    torso = [v for v in bv if abs(v.x - cx) < H * 0.13]
    def ell(z):
        near = [v for v in torso if abs(v.z - z) < 1.2]
        if not near:
            return None
        return ((max(v.x for v in near) - min(v.x for v in near)) / 2, (max(v.y for v in near) - min(v.y for v in near)) / 2,
                (max(v.x for v in near) + min(v.x for v in near)) / 2, (max(v.y for v in near) + min(v.y for v in near)) / 2)
    cache = {}
    moved = 0
    for v in me.vertices:
        if v.co.z >= zt:
            continue
        k = int(v.co.z)
        if k not in cache:
            cache[k] = ell(v.co.z)
        e = cache[k]
        if not e:
            continue
        xr, yr, ex, ey = e
        dx, dy = v.co.x - ex, v.co.y - ey
        r = math.hypot(dx / max(xr, 1), dy / max(yr, 1))
        if r > LIM:
            f = LIM / r
            w = min(1.0, (zt - v.co.z) / 6.0)      # fade in over 6 cm under the tuck line
            f = 1 - (1 - f) * w
            v.co.x = ex + dx * f; v.co.y = ey + dy * f; moved += 1
    me.update(); print("TUCK moved", moved)

# push cloth that is inside the body out to GAP, spread over neighbours so both shell layers move together
tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
push, n = [], 0
for v in bm.verts:
    loc, nrm, _, _ = tree.find_nearest(v.co)
    side = (v.co - loc).dot(nrm) if loc is not None else GAP
    push.append(nrm * (GAP - side) if side < GAP else Vector()); n += side < GAP
for _ in range(8):
    nxt = []
    for v in bm.verts:
        nb = [push[e.other_vert(v).index] for e in v.link_edges]
        avg = sum(nb, Vector()) / len(nb) if nb else Vector()
        p = push[v.index]
        nxt.append(p if p.length >= avg.length else avg)
    push = nxt
for v in bm.verts:
    if PUSH:
        v.co += push[v.index]
bm.to_mesh(me); bm.free()

# close small holes (the AI shell's pin-holes); the big openings (waist, legs) stay open
bm = bmesh.new(); bm.from_mesh(me)
edges, seen, loops = [e for e in bm.edges if e.is_boundary], set(), []
for e in edges:
    if e in seen:
        continue
    loop, stack = [], [e]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x); loop.append(x)
        for v in x.verts:
            stack += [y for y in v.link_edges if y.is_boundary and y not in seen]
    loops.append(loop)
small = [l for l in loops if len(l) < 80]
for l in small:
    bmesh.ops.holes_fill(bm, edges=l, sides=0)
bm.to_mesh(me); bm.free()
print("HOLES filled %d of %d" % (len(small), len(loops)))

# its colour texture
img = None
for m in me.materials:
    if m and m.use_nodes:
        for nd in m.node_tree.nodes:
            if nd.type == "TEX_IMAGE" and nd.image:
                img = nd.image; break
if img:
    img.filepath_raw = out_tex; img.file_format = "PNG"; img.save()

bpy.ops.object.select_all(action="DESELECT"); g.select_set(True)
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True)

# close-up previews: front, side, back (material colours)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
world = bpy.data.worlds.new("w"); sc.world = world; world.color = (0.6, 0.6, 0.6)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sc.collection.objects.link(sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = (zw - zh) * 1.5; cam.data.clip_end = 5000
sc.render.resolution_x, sc.render.resolution_y = 700, 800
tiles = []
for i, ang in enumerate((180, 90, 0)):   # CC5 OBJ: the character faces +Y here
    th = math.radians(ang)
    cam.location = (cx + math.sin(th) * 400, cy - math.cos(th) * 400, (zw + zh) / 2)
    cam.rotation_euler = (math.radians(90), 0, th)
    sc.render.filepath = out_png.replace(".png", "_%d.png" % i)
    bpy.ops.render.render(write_still=True)
print("FIT scale=%.1f sx=%.1f sy=%.1f pushed=%d tex=%s" % (s, sx, sy, n, bool(img)))
