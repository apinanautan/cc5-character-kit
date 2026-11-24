# Blender (headless): CC5 OBJ (cm, Z-up) -> Y-up OBJ for LoadAccessoryWithTransferSkinWeight.  blender -b --python blender\obj_to_yup.py -- <in.obj> <out.obj>
import sys
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=a[0], forward_axis="Y", up_axis="Z")
o = bpy.context.selected_objects[0]
bpy.ops.wm.obj_export(filepath=a[1], export_selected_objects=True, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True)
