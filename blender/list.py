import bpy, sys
fbx = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
for o in bpy.data.objects:
    if o.type == "MESH":
        bb = [o.matrix_world @ __import__("mathutils").Vector(c) for c in o.bound_box]
        zs = [v.z for v in bb]
        print("MESH", o.name, len(o.data.vertices), [u.name for u in o.data.uv_layers], [m.name for m in o.data.materials][:4], round(min(zs), 2), round(max(zs), 2))
