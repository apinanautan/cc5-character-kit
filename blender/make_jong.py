# Blender (headless, CC5 closed): build a chong kraben on a character's own body with Blender cloth simulation.
#   blender -b --python blender\make_jong.py -- <body_tpose.obj> <out.obj> <preview.png> [len=knee|calf] [puff=6]
# The garment starts as the body's own skin from waist to hem (two legs already joined at the crotch, clean
# quads), inflated loose like a chong kraben (thighs most, inner legs less so they don't cross), subdivided,
# then cloth-simulated on the body: waist pinned, hems gathered (shrink) so the legs balloon and the cloth
# drapes into folds. UVs: front / back like a sewing pattern. Output in the same space as the body + previews.
import math, sys
import bmesh, bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
body_path, out_obj, out_png = a[:3]
opt = dict(x.split("=") for x in a[3:] if "=" in x)
PUFF = float(opt.get("puff", 6.0))       # cm off the skin at the thighs
LENGTH = opt.get("len", "knee")
TAIL = opt.get("tail", "1") == "1"
UV_REPEAT = float(opt.get("uvrep", 6))   # fabric repeats across the garment

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=body_path, forward_axis="Y", up_axis="Z")  # same axes as the other CC5 OBJ scripts (else mirrored)
body = bpy.context.selected_objects[0]
body.name = "body"
vs = [v.co.copy() for v in body.data.vertices]
z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
H = z1 - z0
z_waist = z0 + H * 0.60
z_hem = z0 + H * (0.27 if LENGTH == "knee" else 0.22)
z_thigh = z0 + H * 0.42

jong = body.copy(); jong.data = body.data.copy(); jong.name = "jong"
bpy.context.collection.objects.link(jong)
bm = bmesh.new(); bm.from_mesh(jong.data)
bm.verts.ensure_lookup_table()
# biggest connected piece = the body skin (eyes, teeth, lashes ... go)
seen, parts = set(), []
for v in bm.verts:
    if v in seen:
        continue
    stack, part = [v], []
    seen.add(v)
    while stack:
        x = stack.pop(); part.append(x)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in seen:
                seen.add(o); stack.append(o)
    parts.append(part)
parts.sort(key=len, reverse=True)
keep = set(parts[0])
hip_half = max(abs(v.co.x) for v in keep if abs(v.co.z - (z0 + H * 0.52)) < 1.0) + 2.0
drop = [v for v in bm.verts if v not in keep or v.co.z > z_waist + 3 or v.co.z < z_hem - 3 or abs(v.co.x) > hip_half]
bmesh.ops.delete(bm, geom=drop, context="VERTS")
for zc, keep_below in ((z_waist, True), (z_hem, False)):  # straight cut lines (no jagged edge from the body's topology)
    g = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, zc), plane_no=(0, 0, 1),
                           clear_outer=keep_below, clear_inner=not keep_below)
bm.normal_update()


def puff(z):  # how far the cloth stands off the skin: snug at the waist, fullest at the thigh
    t = (z_waist - z) / (z_waist - z_thigh)
    return 1.5 + (PUFF - 1.5) * max(0.0, min(1.0, t))


z_crotch = z0 + H * 0.47


def outward(v):
    """Away from the limb's own axis (the CC5 body's normals can face inwards)."""
    if v.co.z < z_crotch:                 # a leg: its axis is the mean x of that leg at this height
        same = [w.co for w in bm.verts if abs(w.co.z - v.co.z) < 1.0 and (w.co.x > 0) == (v.co.x > 0)]
    else:
        same = [w.co for w in bm.verts if abs(w.co.z - v.co.z) < 1.0]
    c = sum(same, Vector()) / len(same)
    d = Vector((v.co.x - c.x, v.co.y - c.y, 0.0))
    return d.normalized() if d.length else Vector((0, -1, 0))


moves = []
for v in bm.verts:
    d = puff(v.co.z)
    o = outward(v)
    if v.co.z < z_crotch and o.x * v.co.x < 0:
        d *= 0.3 + 0.7 * (1 - abs(o.x))   # inner leg: don't push into the other leg
    moves.append(o * d)
for v, m in zip(bm.verts, moves):
    v.co += m
bm.to_mesh(jong.data); bm.free()
bpy.context.view_layer.objects.active = jong
bpy.ops.object.select_all(action="DESELECT"); jong.select_set(True)
for m in list(jong.modifiers):
    jong.modifiers.remove(m)
sm = jong.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.8; sm.iterations = 6
sub = jong.modifiers.new("sub", "SUBSURF"); sub.levels = 1
bpy.ops.object.modifier_apply(modifier="smooth")
bpy.ops.object.modifier_apply(modifier="sub")

pin = jong.vertex_groups.new(name="pin"); hem = jong.vertex_groups.new(name="hem")
for v in jong.data.vertices:
    if v.co.z > z_waist - 2.5:
        pin.add([v.index], 1.0, "REPLACE")
    if v.co.z < z_hem + 2.5:
        hem.add([v.index], 1.0, "REPLACE")

body.modifiers.new("coll", "COLLISION")
body.collision.thickness_outer = 0.5
cl = jong.modifiers.new("cloth", "CLOTH")
st = cl.settings
st.quality = 10
st.mass = 0.2
st.tension_stiffness = st.compression_stiffness = 10
st.bending_stiffness = 0.15
st.vertex_group_mass = "pin"
st.vertex_group_shrink = "hem"
st.shrink_min = 0.0                       # unshrunk cloth everywhere ...
st.shrink_max = 0.45                      # ... hems (vertex group "hem") gathered -> balloon legs
cl.collision_settings.distance_min = 0.5
cl.collision_settings.use_self_collision = True
cl.collision_settings.self_distance_min = 0.3
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 80
for f in range(1, 81):
    sc.frame_set(f)
bpy.ops.object.modifier_apply(modifier="cloth")
bpy.ops.object.shade_smooth()

# the tucked tail (tail=0 leaves it out): a narrow panel hanging from the front waist, draped over the
# trousers by the same cloth solver, then joined
def add_tail():
    tail_w, tail_h = H * 0.09, (z_waist - z_crotch) * 1.25
    front_y = max(v.co.y for v in jong.data.vertices      # in front of the trousers over the whole tail length
                  if abs(v.co.x) < tail_w and z_waist - tail_h - 2 < v.co.z < z_waist)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=10, y_subdivisions=24, size=1.0)
    tail = bpy.context.active_object; tail.name = "tail"
    tail.scale = (tail_w, tail_h, 1); tail.rotation_euler = (math.radians(90), 0, 0)
    tail.location = (0, front_y + 1.0, z_waist - 1.5 - tail_h / 2)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tpin = tail.vertex_groups.new(name="pin")
    tpin.add([v.index for v in tail.data.vertices if v.co.z > z_waist - 2.5], 1.0, "REPLACE")
    sw = tail.modifiers.new("lay", "SHRINKWRAP")  # lay the panel onto the trousers' curve first
    sw.target = jong; sw.wrap_method = "PROJECT"; sw.use_project_y = True; sw.use_negative_direction = True
    sw.use_positive_direction = False; sw.offset = 0.6
    bpy.context.view_layer.objects.active = tail
    bpy.ops.object.modifier_apply(modifier="lay")
    jong.modifiers.new("coll", "COLLISION"); jong.collision.thickness_outer = 0.3
    tc = tail.modifiers.new("cloth", "CLOTH")
    tc.settings.quality = 8; tc.settings.mass = 0.4; tc.settings.bending_stiffness = 0.4
    tc.settings.vertex_group_mass = "pin"
    tc.settings.shrink_min = 0.12             # a little gather: soft vertical folds
    tc.collision_settings.distance_min = 0.4
    sc.frame_set(1)
    for f in range(1, 61):
        sc.frame_set(f)
    bpy.ops.object.select_all(action="DESELECT"); tail.select_set(True); bpy.context.view_layer.objects.active = tail
    bpy.ops.object.modifier_apply(modifier="cloth")
    bpy.ops.object.shade_smooth()
    jong.modifiers.remove(jong.modifiers["coll"])
    bpy.ops.object.select_all(action="DESELECT"); jong.select_set(True); tail.select_set(True)
    bpy.context.view_layer.objects.active = jong
    bpy.ops.object.join()


if TAIL:
    add_tail()

me = jong.data
xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
x0, x1, zz0, zz1 = min(xs), max(xs), min(zs), max(zs)
size = max(x1 - x0, zz1 - zz0)
for u in list(me.uv_layers):
    me.uv_layers.remove(u)
uv = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    back = poly.normal.y > 0
    for li in poly.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        u = ((x1 - co.x) if back else (co.x - x0)) / size
        uv.data[li].uv = ((0.02 + u * 0.46 + (0.5 if back else 0.0)) * UV_REPEAT,
                          (0.02 + (co.z - zz0) / size * 0.96) * UV_REPEAT)
jong.data.materials.clear()
# all faces facing out (part of the body's skin came through facing in; CC5 draws one side only)
bpy.ops.object.select_all(action="DESELECT"); jong.select_set(True); bpy.context.view_layer.objects.active = jong
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True)  # Y-up: what CC5 LoadAccessory expects

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 0.6; cam.data.clip_end = 2000
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "OBJECT"
jong.color = (0.45, 0.30, 0.18, 1); body.color = (0.85, 0.68, 0.55, 1)
sc.render.resolution_x, sc.render.resolution_y = 600, 800
for tag, y, rz in (("back", -300, 0), ("front", 300, 180)):
    cam.location = (0, y, z0 + H * 0.45); cam.rotation_euler = (math.radians(90), 0, math.radians(rz))
    sc.render.filepath = out_png.replace(".png", "_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
print("JONG %d faces, H=%.1f waist=%.1f hem=%.1f" % (len(me.polygons), H, z_waist, z_hem))
