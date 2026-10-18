# Blender (headless): smooth one garment from a CC5 character FBX in its CURRENT pose and export the bare mesh for CC5 LoadClotheFromFbx.
#   blender -b --python blender_smooth_cloth.py -- <char.fbx> <mesh name> <out.fbx> <out_preview.png>
# Sleeves relaxed + subdivision (UV kept) + smooth shading, edited in the rest shape; skeleton and skin weights kept.
import bpy, math, sys
from mathutils import Vector

fbx, name, out, preview = sys.argv[sys.argv.index("--") + 1:][:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
obj = bpy.data.objects[name]
arm = obj.find_armature()
for o in list(bpy.data.objects):
    if o not in (obj, arm):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
arm_mod = next((m for m in obj.modifiers if m.type == "ARMATURE"), None)
# keep skeleton + skin weights (CC5 LoadClotheFromFbx only accepts skinned cloth); edit the rest shape only
if arm_mod:
    arm_mod.show_viewport = False
# smooth only the sleeves: vertices further than 60% of the shoulder half-width from the body center line
mw = obj.matrix_world
xs = [(mw @ v.co).x for v in obj.data.vertices]
cx = (min(xs) + max(xs)) / 2; half = (max(xs) - min(xs)) / 2
vg = obj.vertex_groups.new(name="sleeves")
for v, x in zip(obj.data.vertices, xs):
    t = (abs(x - cx) / half - 0.35) / 0.25  # 0 at 35% -> 1 at 60% (soft blend)
    if t > 0:
        vg.add([v.index], min(1.0, t), "REPLACE")
sm = obj.modifiers.new("relax", "SMOOTH"); sm.factor = 0.6; sm.iterations = 8; sm.vertex_group = "sleeves"
sub = obj.modifiers.new("subd", "SUBSURF"); sub.levels = 1; sub.render_levels = 1; sub.uv_smooth = "PRESERVE_BOUNDARIES"
for m in (sm, sub):
    bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0 if m is sm else 1)
    bpy.ops.object.modifier_apply(modifier=m.name)
obj.vertex_groups.remove(obj.vertex_groups["sleeves"])
if arm_mod:
    arm_mod.show_viewport = True
bpy.ops.object.shade_smooth()
print("VERTS", len(obj.data.vertices))
# preview render (front, clay)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"; sc.render.resolution_x = sc.render.resolution_y = 1024
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); w.use_nodes = True; sc.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.85, 0.85, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))); hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
c = (lo + hi) / 2; size = max(hi - lo) * 1.15
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = size; sc.camera = cam
cam.location = c + Vector((0, -size * 3, 0)); cam.rotation_euler = (math.radians(90), 0, 0)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (math.radians(60), 0, math.radians(20))
mat = bpy.data.materials.new("clay"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
keep = [s.material for s in obj.material_slots]
obj.data.materials.clear(); obj.data.materials.append(mat)
sc.render.filepath = preview; bpy.ops.render.render(write_still=True)
obj.data.materials.clear()
for m in keep:
    obj.data.materials.append(m)
bpy.ops.object.select_all(action="DESELECT"); obj.select_set(True); arm.select_set(True)
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=False)
print("EXPORTED", out)
