# Blender: render textured OBJs side by side (front + a close-up) to compare before / after.
#   blender -b --python blender\compare_render.py -- <out.png> <a.obj> <a.png> <b.obj> <b.png> ...
import math, sys
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
out, pairs = a[0], list(zip(a[1::2], a[2::2]))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
objs = []
for i, (obj, tex) in enumerate(pairs):
    bpy.ops.wm.obj_import(filepath=obj, forward_axis="Y", up_axis="Z")
    o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new("m%d" % i); m.use_nodes = True
    n = m.node_tree.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(tex)
    m.node_tree.links.new(n.outputs["Color"], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    objs.append(o)
bb = [o.matrix_world @ Vector(c) for c in objs[0].bound_box]
lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
size = (hi - lo).length
for i, o in enumerate(objs):
    o.location.x += i * size * 1.1
sc.render.engine = "BLENDER_EEVEE_NEXT"
w = bpy.data.worlds.new("w"); sc.world = w; w.color = (0.55, 0.55, 0.55)
for ang in (40, -50):
    s = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); s.data.energy = 2.5
    s.rotation_euler = (math.radians(55), 0, math.radians(ang)); sc.collection.objects.link(s)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.clip_end = 10000
ctr = (lo + hi) / 2
# Y-up OBJ imported with Y/Z: the garment stands along Blender -Y; look at it from +Z? find the tall axis
dims = hi - lo
tall = max(range(3), key=lambda k: dims[k])
cam.data.ortho_scale = max(dims) * 1.15 * 1.0
span = size * 1.1 * (len(objs) - 1)
target = ctr + Vector((span / 2, 0, 0))
sc.render.resolution_x, sc.render.resolution_y = 900 * len(objs), 1000
cam.data.ortho_scale = max(dims) * 1.1 * len(objs)
views = {"front": Vector((0, -1, 0)), "front2": Vector((0, 0, 1)), "front3": Vector((0, 1, 0))}
for name, d in (("view", Vector((0, 0, 1)) if tall == 1 else Vector((0, -1, 0))),):
    cam.location = target + d * size * 4
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y" if tall == 2 else "Z").to_euler()
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
print("RENDER", out, "tall axis", tall)
