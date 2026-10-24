# Blender headless: rebuild an AI garment as a clean, even mesh and bake its texture onto it.
#   blender -b --python blender/remesh_garment.py -- <in.obj (Y-up, textured)> <out.obj> [voxel_cm] [faces]
# AI meshes are messy thick shells (torn pieces, uneven triangles) that break when skinned. Voxel remesh makes one
# closed, even surface; decimate keeps it light; Smart UV + Cycles bake copies the AI texture onto the new mesh.
import bpy, os, sys

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[:2]
voxel = float(a[2]) if len(a) > 2 else 0.9  # coarser = far less RAM
faces = int(a[3]) if len(a) > 3 else 16000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis="NEGATIVE_Z", up_axis="Y")
orig = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
orig.name = "orig"
bpy.ops.object.select_all(action="DESELECT")
orig.select_set(True)
bpy.context.view_layer.objects.active = orig
bpy.ops.object.duplicate()
new = bpy.context.view_layer.objects.active
new.name = "garment"
new.data.materials.clear()

m = new.modifiers.new("remesh", "REMESH")
m.mode = "VOXEL"; m.voxel_size = voxel; m.adaptivity = 0.0; m.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier="remesh")
n_vox = len(new.data.polygons)
if n_vox > faces:
    d = new.modifiers.new("dec", "DECIMATE"); d.ratio = faces / n_vox
    bpy.ops.object.modifier_apply(modifier="dec")
sm = new.modifiers.new("smooth", "SMOOTH"); sm.iterations = 2; sm.factor = 0.4
bpy.ops.object.modifier_apply(modifier="smooth")
print("REMESH voxel=%.2f %d -> %d faces" % (voxel, n_vox, len(new.data.polygons)))

bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
bpy.ops.object.mode_set(mode="OBJECT")

# bake the AI colour map from the original onto the new mesh
img = bpy.data.images.new("garment_diffuse", 1024, 1024)
mat = bpy.data.materials.new("garment"); mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
mat.node_tree.nodes.active = tex
new.data.materials.append(mat)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.device = "GPU" if os.environ.get("BAKE_GPU") else "CPU"
bake = scene.render.bake
bake.use_selected_to_active = True
bake.cage_extrusion = voxel * 3
bake.max_ray_distance = voxel * 6
bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
bpy.ops.object.select_all(action="DESELECT")
orig.select_set(True); new.select_set(True)
bpy.context.view_layer.objects.active = new
bpy.ops.object.bake(type="DIFFUSE", margin=8)
tex_path = os.path.splitext(out)[0] + "_diffuse.png"
img.filepath_raw = tex_path; img.file_format = "PNG"; img.save()
print("BAKED", tex_path)

bpy.data.objects.remove(orig)
bpy.ops.object.select_all(action="DESELECT")
new.select_set(True)
bpy.context.view_layer.objects.active = new
bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                      export_materials=True, path_mode="RELATIVE", export_normals=True, export_uv=True)
print("WROTE", out)
