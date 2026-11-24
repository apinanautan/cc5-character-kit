"""QA renders: one contact sheet of a mesh (optionally on the body) from several views, Workbench + cavity so
pits, holes, blotches and wrinkles are visible.
  blender -b -P render_views.py -- mesh=<a.glb|obj> out=<sheet.png> [body=<body_tpose.obj>] [gltf_to_cc=1]
         [views=front,back,left,three_quarter,top_neck] [res=700] [color=0.55,0.7,0.85]
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from mathutils import Vector

A = args(); reset()
objs = [o for o in import_any(A["mesh"]) if o.type == "MESH"]
garment = objs
if A.get("body"):
    b = import_obj(A["body"], use_split_groups=True)
    body = [o for o in b if o.type == "MESH" and o.name.startswith("CC_Base_Body")]
    for o in b:
        if o not in body: bpy.data.objects.remove(o)
else:
    body = []
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"; sh.show_cavity = True; sh.cavity_type = "BOTH"
sh.curvature_ridge_factor = 1.0; sh.curvature_valley_factor = 1.0
sh.show_backface_culling = False
sc.display.shading.background_type = "VIEWPORT" if hasattr(sc.display.shading, "background_type") else None
col = tuple(float(x) for x in A.get("color", "0.55,0.7,0.85").split(","))
gm = bpy.data.materials.new("G"); gm.diffuse_color = (*col, 1)
bm = bpy.data.materials.new("B"); bm.diffuse_color = (0.85, 0.62, 0.52, 1)
for o in garment:
    o.data.materials.clear(); o.data.materials.append(gm)
for o in body:
    o.data.materials.clear(); o.data.materials.append(bm)
lo, hi = bbox(garment)
c = (lo + hi) / 2; size = max(hi - lo) * 1.08
res = int(A.get("res", 700))
sc.render.resolution_x = sc.render.resolution_y = res
w = bpy.data.worlds.new("W"); sc.world = w; w.color = (0.92, 0.92, 0.92)
up_z = A.get("gltf_to_cc") != "1" and (hi.z - lo.z) >= (hi.y - lo.y) * 0.6
# glTF imports are converted to Z-up by Blender, CC OBJ we import Z-up too -> front is -Y in both.
dirs = {"front": (0, -1, 0), "back": (0, 1, 0), "left": (1, 0, 0), "right": (-1, 0, 0),
        "three_quarter": (0.7, -0.7, 0.25), "back_quarter": (-0.7, 0.7, 0.25), "top_neck": (0, -0.35, 1)}
views = A.get("views", "front,back,left,three_quarter").split(",")
tmp = []
for v in views:
    if v.startswith("zoom:"):            # zoom:<name>:x,y,z:scale -> close-up at a point (world units)
        _, name, p, s = v.split(":")
        cc = Vector(float(t) for t in p.split(",")); cam = ortho_camera(cc, float(s), (0.3, -1, 0.2), "C_" + name)
    else:
        cam = ortho_camera(c, size, dirs[v], "C_" + v)
    sc.camera = cam
    p = os.path.join(os.path.dirname(A["out"]), f"_view_{v.replace(':', '_').replace(',', '_')}.png")
    render(p); tmp.append((v, p))
# contact sheet
imgs = [bpy.data.images.load(p) for _, p in tmp]
W = res * len(imgs)
sheet = bpy.data.images.new("sheet", W, res)
import numpy as np
buf = np.zeros((res, W, 4), np.float32)
for i, im in enumerate(imgs):
    px = np.array(im.pixels[:], np.float32).reshape(res, res, 4)
    buf[:, i * res:(i + 1) * res] = px
sheet.pixels = buf.ravel()
sheet.filepath_raw = A["out"]; sheet.file_format = "PNG"; sheet.save()
for _, p in tmp: os.remove(p)
print("SHEET", A["out"], "faces", sum(len(o.data.polygons) for o in garment))
