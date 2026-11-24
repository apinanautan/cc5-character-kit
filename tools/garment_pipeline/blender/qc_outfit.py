# Headless: render the body wearing several garments (each with its baked diffuse / optional normal map).
#   blender -b -P qc_outfit.py -- <body_tpose.obj Z-up> <qc_prefix ABS> <garment.obj>|<diffuse.png>|<normal.png or -> ...
import bpy, sys
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
body_p, qc = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=body_p, forward_axis="Y", up_axis="Z", use_split_groups=True)
skin = bpy.data.materials.new("skin"); skin.use_nodes = True
next(n for n in skin.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.55, 0.38, 0.3, 1)
for o in list(sc.objects):
    if o.type != "MESH": continue
    if "BBJ" in o.name or "Shape" in o.name and "CC_Base" not in o.name: bpy.data.objects.remove(o); continue   # old clothes off
    if o.name.startswith("default"): bpy.data.objects.remove(o); continue         # our own garment re-exported from CC5
    o.data.materials.clear(); o.data.materials.append(skin)
    if "skirt" in o.name.lower() or "pants" in o.name.lower():                  # library bottoms worn in CC5: plain khaki
        km = bpy.data.materials.new("lib"); km.use_nodes = True
        next(n for n in km.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.42, 0.42, 0.22, 1)
        o.data.materials.clear(); o.data.materials.append(km)
for spec in a[2:]:
    g, d, n = (spec.split("|") + ["-", "-"])[:3]
    before = set(sc.objects)
    bpy.ops.wm.obj_import(filepath=g, forward_axis="NEGATIVE_Z", up_axis="Y")
    ob = [o for o in sc.objects if o not in before][0]
    m = bpy.data.materials.new(ob.name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED"); bsdf.inputs["Roughness"].default_value = 0.75
    if d != "-":
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(d); nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if n != "-":
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(n); t.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    ob.data.materials.clear(); ob.data.materials.append(m)
try: sc.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError: sc.render.engine = "BLENDER_EEVEE"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
for rot, en in (((0.9, 0, 0.6), 3.0), ((1.1, 0, -2.4), 1.8)):
    s = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); s.data.energy = en; s.rotation_euler = rot; sc.collection.objects.link(s)
sc.render.resolution_x, sc.render.resolution_y = 800, 1200; sc.view_settings.view_transform = "Standard"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_end = 10000; cam.data.lens = 70
for tag, d_, aim_z in (("front", (0, -1, 0.05), 95), ("side", (1, -0.15, 0.05), 95), ("back", (0, 1, 0.05), 95), ("waist", (0.3, -1, 0.1), 105)):
    aim = Vector((0, 0, aim_z)); dist = 330 if tag != "waist" else 120
    cam.location = aim + Vector(d_).normalized() * dist
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = qc + tag + ".png"; bpy.ops.render.render(write_still=True)
