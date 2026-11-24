"""Shared Blender helpers for the garment pipeline (run with blender -b -P script.py -- args)."""
import bpy, sys, json, math, os
from mathutils import Vector

def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return dict(x.split("=", 1) for x in a)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# CC5 ExportObjFile writes Z-up centimetres: import/export with these axes so nothing is rotated.
CC_AXES = dict(up_axis="Z", forward_axis="Y")

def import_obj(path, **kw):
    kw = {**CC_AXES, **kw}
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path, **kw)
    return [o for o in bpy.data.objects if o not in before]

def import_any(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".obj": bpy.ops.wm.obj_import(filepath=path)
    elif ext in (".glb", ".gltf"): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".ply": bpy.ops.wm.ply_import(filepath=path)
    elif ext == ".fbx": bpy.ops.import_scene.fbx(filepath=path)
    else: raise ValueError(ext)
    return [o for o in bpy.data.objects if o not in before]

def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi

def flat_mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m

def setup_render(res=(1024, 1024), bg=(1, 1, 1), engine="BLENDER_EEVEE"):
    sc = bpy.context.scene
    for e in (engine, "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try: sc.render.engine = e; break
        except TypeError: pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bgn = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bgn.inputs[0].default_value = (*bg, 1); bgn.inputs[1].default_value = float(os.environ.get("GP_WORLD", "0.35"))
    try: sc.view_settings.view_transform = "Standard"
    except TypeError: pass
    return sc

def ortho_camera(center, scale, direction=(0, -1, 0), name="Cam"):
    cam = bpy.data.cameras.new(name); cam.type = "ORTHO"; cam.ortho_scale = scale
    o = bpy.data.objects.new(name, cam); bpy.context.scene.collection.objects.link(o)
    d = Vector(direction).normalized(); o.location = Vector(center) + d * 10
    o.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler(); cam.clip_end = 100
    bpy.context.scene.camera = o
    return o

def sun(rot=(0.9, 0.2, 0.4), energy=3.0):
    l = bpy.data.lights.new("Sun", "SUN"); l.energy = energy
    o = bpy.data.objects.new("Sun", l); o.rotation_euler = rot; bpy.context.scene.collection.objects.link(o)
    return o

def render(path):
    bpy.context.scene.render.filepath = path; bpy.ops.render.render(write_still=True)
