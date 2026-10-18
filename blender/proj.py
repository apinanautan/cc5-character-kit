# Blender (headless) multi-view texture projection onto a garment's EXISTING UV.
#   blender -b --python blender_proj.py -- render <fbx> <mesh name> <out dir>
#       -> view_0..3.png (front/right/back/left, orthographic clay renders) + views.json
#   blender -b --python blender_proj.py -- bake <fbx> <mesh name> <out dir> <size>
#       -> reads painted_0..3.png, projects each onto the mesh, blends by facing angle, bakes baked.png in UV Channel0
import bpy, json, math, os, sys
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
mode, fbx, name, out = a[:4]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
obj = bpy.data.objects[name]
_mw = obj.matrix_world.copy()
obj.parent = None
obj.matrix_world = _mw
for o in list(bpy.data.objects):
    if o is not obj:
        bpy.data.objects.remove(o, do_unlink=True)
obj.modifiers.clear()
bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
center = (lo + hi) / 2
size = max(hi - lo) * 1.15
VIEWS = [0, 180]  # front and back only (user: 2 GPT images per garment)


def view_dirs(deg):
    if deg == "top":
        return Vector((0, 0, 1)), Vector((1, 0, 0))
    r = math.radians(deg)
    d = Vector((math.sin(r), -math.cos(r), 0))  # camera position direction from center
    right = Vector((math.cos(r), math.sin(r), 0))
    return d, right


scene = bpy.context.scene
if mode == "render":
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("w"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.85, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = w
    mat = bpy.data.materials.new("clay"); mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1)
    obj.data.materials.clear(); obj.data.materials.append(mat)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = size; scene.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
    sun.data.energy = 3
    info = []
    for i, deg in enumerate(VIEWS):
        d, right = view_dirs(deg)
        cam.location = center + d * size * 3
        if deg == "top":
            cam.rotation_euler = (0, 0, 0); sun.rotation_euler = (math.radians(20), 0, 0)
        else:
            cam.rotation_euler = (math.radians(90), 0, math.radians(deg))
            sun.rotation_euler = (math.radians(60), 0, math.radians(deg + 20))
        scene.render.filepath = os.path.join(out, "view_%d.png" % i)
        bpy.ops.render.render(write_still=True)
        info.append({"deg": deg})
    json.dump({"center": list(center), "size": size, "views": info}, open(os.path.join(out, "views.json"), "w"))
else:
    px = int(a[4]) if len(a) > 4 else 2048
    me = obj.data
    base_uv = me.uv_layers[0].name
    me.uv_layers.active = me.uv_layers[0]
    mw = obj.matrix_world
    # projection UVs per view (orthographic)
    for i, deg in enumerate(VIEWS):
        d, right = view_dirs(deg)
        up = Vector((0, 1, 0)) if deg == "top" else Vector((0, 0, 1))
        uvl = me.uv_layers.new(name="proj_%d" % i)
        for loop in me.loops:
            p = mw @ me.vertices[loop.vertex_index].co - center
            uvl.data[loop.index].uv = (p.dot(right) / size + 0.5, p.dot(up) / size + 0.5)
    me.uv_layers.active = me.uv_layers[base_uv]
    mat = bpy.data.materials.new("proj"); mat.use_nodes = True
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    N.clear()
    outn = N.new("ShaderNodeOutputMaterial"); emis = N.new("ShaderNodeEmission")
    geo = N.new("ShaderNodeNewGeometry")
    # facing weight from horizontal direction center->point (robust to flipped/inner normals)
    sub = N.new("ShaderNodeVectorMath"); sub.operation = "MULTIPLY"
    L.new(geo.outputs["Position"], sub.inputs[0]); sub.inputs[1].default_value = (1, 1, 0)
    off = N.new("ShaderNodeVectorMath"); off.operation = "SUBTRACT"
    L.new(sub.outputs[0], off.inputs[0]); off.inputs[1].default_value = (center.x, center.y, 0)
    radial = N.new("ShaderNodeVectorMath"); radial.operation = "NORMALIZE"
    L.new(off.outputs[0], radial.inputs[0])
    acc_c = None; acc_w = None
    for i, deg in enumerate(VIEWS):
        d, _ = view_dirs(deg)
        img = bpy.data.images.load(os.path.join(out, "painted_%d.png" % i))
        tex = N.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "EXTEND"
        uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "proj_%d" % i
        L.new(uvn.outputs[0], tex.inputs[0])
        dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = d
        L.new((geo.outputs["Normal"] if deg == "top" else radial.outputs[0]), dot.inputs[0])
        cl = N.new("ShaderNodeMath"); cl.operation = "MAXIMUM"; cl.inputs[1].default_value = 0.15
        L.new(dot.outputs["Value"], cl.inputs[0])
        pw = N.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 2.0
        L.new(cl.outputs[0], pw.inputs[0])
        mul = N.new("ShaderNodeMixRGB"); mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
        L.new(tex.outputs[0], mul.inputs[1]); L.new(pw.outputs[0], mul.inputs[2])
        if acc_c is None:
            acc_c, acc_w = mul.outputs[0], pw.outputs[0]
        else:
            ac = N.new("ShaderNodeMixRGB"); ac.blend_type = "ADD"; ac.inputs[0].default_value = 1.0
            L.new(acc_c, ac.inputs[1]); L.new(mul.outputs[0], ac.inputs[2]); acc_c = ac.outputs[0]
            aw = N.new("ShaderNodeMath"); aw.operation = "ADD"
            L.new(acc_w, aw.inputs[0]); L.new(pw.outputs[0], aw.inputs[1]); acc_w = aw.outputs[0]
    eps = N.new("ShaderNodeMath"); eps.operation = "MAXIMUM"; eps.inputs[1].default_value = 1e-4
    L.new(acc_w, eps.inputs[0])
    div = N.new("ShaderNodeMixRGB"); div.blend_type = "DIVIDE"; div.inputs[0].default_value = 1.0
    L.new(acc_c, div.inputs[1]); L.new(eps.outputs[0], div.inputs[2])
    L.new(div.outputs[0], emis.inputs[0]); L.new(emis.outputs[0], outn.inputs[0])
    target = bpy.data.images.new("baked", px, px)
    tn = N.new("ShaderNodeTexImage"); tn.image = target; N.active = tn
    me.materials.clear(); me.materials.append(mat)
    scene.render.engine = "CYCLES"; scene.cycles.samples = 1; scene.cycles.device = "CPU"
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.bake(type="EMIT", margin=16, uv_layer=base_uv)
    target.filepath_raw = os.path.join(out, "baked.png"); target.file_format = "PNG"; target.save()
    print("BAKED", os.path.join(out, "baked.png"))
