# Blender (headless): reduce an OBJ to about <target> faces, keeping UVs (textures stay put) and the overall shape.
#   blender -b --python blender\decimate_obj.py -- <in.obj> <out.obj> <target_faces>
# Collapse decimation, UV seams and open borders (hems, cuffs) are protected so edges don't shrink.
import bpy, sys

a = sys.argv[sys.argv.index("--") + 1:]
src, dst, target = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = obj
before = len(obj.data.polygons)
if before > target:
    # mark UV seams so collapse keeps UV islands intact
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    m = obj.modifiers.new("dec", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = max(0.02, target / before)
    m.use_collapse_triangulate = False
    m.delimit = {"SEAM", "UV"}
    bpy.ops.object.modifier_apply(modifier=m.name)
after = len(obj.data.polygons)
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.wm.obj_export(filepath=dst, export_selected_objects=True, forward_axis="Y", up_axis="Z",
                      export_materials=False, export_normals=True, export_uv=True, export_triangulated_mesh=False)
print("FACES", before, "->", after)
