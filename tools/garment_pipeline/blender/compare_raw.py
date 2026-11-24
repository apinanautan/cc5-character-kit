# Headless: render several raw GLBs with the same Workbench lighting (front / back / chest close-up) for comparison.
#   blender -b -P compare_raw.py -- <out_prefix> <a.glb> <b.glb> ...   -> <out_prefix><i>_<view>.png
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
pre, files = a[0], a[1:]
for i, f in enumerate(files):
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=f)
    obs = [o for o in sc.objects if o.type == "MESH"]
    for o in obs:
        for p in o.data.polygons: p.use_smooth = False
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2; size = max(hi - lo)
    print("MESH", f, sum(len(o.data.polygons) for o in obs), "faces")
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "SINGLE"
    sc.display.shading.single_color = (0.55, 0.75, 0.78)
    sc.render.resolution_x = sc.render.resolution_y = 900
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"
    # glTF import is Z-up in Blender, model front faces -Y
    for tag, d, scale, aim in (("front", Vector((0, -1, 0)), 1.1, c), ("back", Vector((0, 1, 0)), 1.1, c),
                               ("close", Vector((0, -1, 0.1)), 0.35, c + Vector((0, 0, size * 0.18)))):
        cam.data.ortho_scale = size * scale
        cam.location = aim + d.normalized() * size * 3
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"{pre}{i}_{tag}.png"; bpy.ops.render.render(write_still=True)
