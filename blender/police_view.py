# Blender (headless): look at the exported police garments (OBJ cm, Z-up) with their diffuse maps, one render per piece.
#   blender -b --python blender\police_view.py -- <folder>
import math, os, sys
import bpy

d = sys.argv[sys.argv.index("--") + 1]
pieces = [("cloth0_mesh_node_0.obj", "tex/c0_mesh_node_0_Material_001_diff.png"),
          ("cloth1_Skirt.obj", "tex/c1_Skirt_Material_001_diff.png"),
          ("cloth3_texture_pbr_v128.obj", "tex/c3_default_Material_diff.png")]
for obj, tex in pieces:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=os.path.join(d, obj), forward_axis="Y", up_axis="Z")
    o = bpy.context.selected_objects[0]
    m = bpy.data.materials.new("m"); m.use_nodes = True
    t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(d, tex))
    m.node_tree.links.new(t.outputs["Color"], m.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    o.data.materials.clear(); o.data.materials.append(m)
    zs = [v.co.z for v in o.data.vertices]; xs = [v.co.x for v in o.data.vertices]
    print(obj, "z %.1f..%.1f  x %.1f..%.1f  verts %d" % (min(zs), max(zs), min(xs), max(xs), len(zs)))
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"; sc.display.shading.color_type = "TEXTURE"
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = (max(zs) - min(zs)) * 1.15 if (max(zs)-min(zs)) > (max(xs)-min(xs)) else (max(xs)-min(xs)) * 1.15
    cam.data.clip_end = 5000
    cam.location = ((max(xs)+min(xs))/2, -500, (max(zs)+min(zs))/2); cam.rotation_euler = (math.radians(90), 0, 0)
    sc.render.resolution_x, sc.render.resolution_y = 700, 700
    sc.render.filepath = os.path.join(d, "view_" + obj.replace(".obj", ".png"))
    bpy.ops.render.render(write_still=True)
