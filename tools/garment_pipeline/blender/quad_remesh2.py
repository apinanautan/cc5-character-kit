# Headless: messy TRELLIS mesh -> fine voxel remesh (watertight, smooth) -> QuadriFlow quads -> close-up QC renders.
# blender -b -P quad_remesh2.py -- <in.glb> <out.glb> <voxel> <quad_faces> <qc_prefix>
import bpy, sys, time, math, mathutils
a = sys.argv[sys.argv.index("--") + 1:]; src, dst, vox, nq, qc = a[0], a[1], float(a[2]), int(a[3]), a[4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
bpy.context.view_layer.objects.active = o; o.select_set(True); t = time.time()
print("dims", tuple(round(d, 3) for d in o.dimensions))
o.data.remesh_voxel_size = vox * max(o.dimensions); o.data.use_remesh_fix_poles = True
bpy.ops.object.voxel_remesh()
sm = o.modifiers.new("sm", "LAPLACIANSMOOTH"); sm.lambda_factor = float(a[5]) if len(a) > 5 else 0.0; sm.iterations = 3; sm.use_volume_preserve = True
if sm.lambda_factor: bpy.ops.object.modifier_apply(modifier="sm")
else: o.modifiers.remove(sm)
print("voxel", len(o.data.polygons), round(time.time() - t), "s")
# keep largest piece
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
parts = [x for x in bpy.context.scene.objects if x.type == "MESH"]
o = max(parts, key=lambda x: len(x.data.polygons))
for x in parts:
    if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
m = o.modifiers.new("dec", "DECIMATE"); m.ratio = nq / len(o.data.polygons); bpy.ops.object.modifier_apply(modifier="dec")
import bmesh; bm = bmesh.new(); bm.from_mesh(o.data); r = ("boundary", sum(e.is_boundary for e in bm.edges), "nonmanifold", sum(not e.is_manifold for e in bm.edges)); bm.free()
print("decimated", r, len(o.data.polygons), round(time.time() - t), "s")
bpy.ops.object.shade_smooth()
bpy.ops.export_scene.gltf(filepath=dst, use_selection=True, export_materials="NONE"); print("WROTE", dst)
# QC renders: full + close-up, solid shading with wire-free studio light
sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "SINGLE"; sc.display.shading.single_color = (0.25, 0.55, 0.58)
sc.render.resolution_x = sc.render.resolution_y = 1100
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
c = o.matrix_world @ (sum((mathutils.Vector(b) for b in o.bound_box), mathutils.Vector()) / 8)
R = max(o.dimensions)
for tag, d, dist, aim in (("front", (0, -1, 0), 1.6, c), ("back", (0, 1, 0), 1.6, c),
                          ("close", (0, -1, 0), 0.6, c + mathutils.Vector((0, 0, 0.2 * R)))):
    cam.location = aim + mathutils.Vector(d) * dist * R
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = qc + tag + ".png"; bpy.ops.render.render(write_still=True)
