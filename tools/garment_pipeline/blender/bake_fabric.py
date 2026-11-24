# Headless: bake a tileable fabric photo onto the garment's UVs as its diffuse map (box projection in cm, so the
# weave has one real-world scale everywhere, no UV stretching). Button UV cell (from add_buttons) is painted a solid colour.
#   blender -b -P bake_fabric.py -- <garment.obj Y-up> <fabric.jpg> <out_diffuse.png> <tile_cm> <size> <btn_u> <btn_v> <btn_hex> [normal.png qc_prefix]
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
obj_p, fab_p, out_p = a[:3]; TILE = float(a[3]); SIZE = int(a[4]); BHEX = a[7]
# btn_u = <garment>.buttons_uv.json (from add_buttons.py) -> a button picture is painted in that square; '-' = no buttons
BJ = __import__("json").load(open(a[5])) if a[5].endswith(".json") else None
BU, BV = (BJ["u"], BJ["v"]) if BJ else (float(a[5]), float(a[6]))
nrm_p = a[8] if len(a) > 8 else None; qc = a[9] if len(a) > 9 else None
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=obj_p, forward_axis="NEGATIVE_Z", up_axis="Y")
gar = [o for o in sc.objects if o.type == "MESH"][0]
from mathutils import Matrix
gar.data.transform(gar.matrix_world); gar.matrix_world = Matrix.Identity(4)

mat = bpy.data.materials.new("fab"); mat.use_nodes = True; gar.data.materials.clear(); gar.data.materials.append(mat)
nt = mat.node_tree; L = nt.links; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1 / TILE,) * 3
L.new(tc.outputs["Object"], mp.inputs["Vector"])
fab = nt.nodes.new("ShaderNodeTexImage"); fab.image = bpy.data.images.load(fab_p)
fab.projection = "BOX"; fab.projection_blend = 0.25
L.new(mp.outputs["Vector"], fab.inputs["Vector"])
emi = nt.nodes.new("ShaderNodeEmission"); L.new(fab.outputs["Color"], emi.inputs["Color"])
out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"); L.new(emi.outputs["Emission"], out.inputs["Surface"])
img = bpy.data.images.new("diffuse", SIZE, SIZE); tgt = nt.nodes.new("ShaderNodeTexImage"); tgt.image = img
nt.nodes.active = tgt
try: sc.render.engine = "CYCLES"
except TypeError: pass
sc.cycles.samples = 1; sc.render.bake.margin = 8
try:
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    bpy.context.preferences.addons["cycles"].preferences.get_devices(); sc.cycles.device = "GPU"
except Exception: pass
bpy.context.view_layer.objects.active = gar; gar.select_set(True)
bpy.ops.object.bake(type="EMIT")
# button picture
import numpy as np, math
W = H = SIZE
if BHEX != "-":
    px = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
    c = np.array([int(BHEX[i:i + 2], 16) / 255 for i in (0, 2, 4)]) ** 2.2          # sRGB -> linear (image is linear float)
    if BJ:
        half = BJ["half"]; g = BJ["grid"] / 64
        y0, x0, S = int(BJ["cell"][0] / 64 * H), int(BJ["cell"][1] / 64 * W), int(g * W)
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        u = ((x0 + xx + 0.5) / W - BU) / half; v = ((y0 + yy + 0.5) / H - BV) / half; rr = np.hypot(u, v)
        shade = 1.0 - 0.10 * np.exp(-((rr - 0.80) / 0.06) ** 2) - 0.08 * np.clip(1 - rr / 0.66, 0, 1) - 0.25 * (rr > 0.97)
        holes = np.zeros_like(rr)
        for k in range(4):
            ang = math.pi / 4 + k * math.pi / 2
            holes = np.maximum(holes, np.clip((0.12 - np.hypot(u - 0.30 * math.cos(ang), v - 0.30 * math.sin(ang))) / 0.02, 0, 1))
        col = c[None, None, :] * shade[..., None] * (1 - 0.85 * holes[..., None])
        px[y0:y0 + S, x0:x0 + S, :3] = col; px[y0:y0 + S, x0:x0 + S, 3] = 1
    else:                                                  # old layout: one flat colour cell
        cx, cy, hf = int(BU * W), int(BV * H), max(4, W // 128)
        px[cy - hf:cy + hf, cx - hf:cx + hf, :3] = c; px[cy - hf:cy + hf, cx - hf:cx + hf, 3] = 1
    img.pixels[:] = px.ravel()
img.filepath_raw = out_p; img.file_format = "PNG"; img.save()
print("BAKED", out_p, SIZE)

if qc:   # QC render with the baked diffuse + normal map, like CC5 will see it
    for n in [emi, fab, mp, tc]: nt.nodes.remove(n)
    L.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    d = nt.nodes.new("ShaderNodeTexImage"); d.image = bpy.data.images.load(out_p); L.new(d.outputs["Color"], bsdf.inputs["Base Color"])
    if nrm_p:
        ni = nt.nodes.new("ShaderNodeTexImage"); ni.image = bpy.data.images.load(nrm_p); ni.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); L.new(ni.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.7
    try: sc.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError: sc.render.engine = "BLENDER_EEVEE"
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    for rot, en in (((0.9, 0, 0.6), 3.0), ((1.1, 0, -2.2), 1.5)):
        s = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); s.data.energy = en; s.rotation_euler = rot; sc.collection.objects.link(s)
    sc.render.resolution_x = sc.render.resolution_y = 1000; sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam; cam.data.clip_end = 10000
    bb = [gar.matrix_world @ v.co for v in gar.data.vertices]; ctr = (Vector((min(p.x for p in bb), min(p.y for p in bb), min(p.z for p in bb))) + Vector((max(p.x for p in bb), max(p.y for p in bb), max(p.z for p in bb)))) / 2
    chest = ctr + Vector((0, 0, (max(p.z for p in bb) - ctr.z) * 0.45))
    for tag, dist, aim, d_ in (("front", 120, ctr, (0, -1, 0.05)), ("back", 120, ctr, (0, 1, 0.05)), ("chest", 40, chest, (0.2, -1, 0.1))):
        cam.location = aim + Vector(d_).normalized() * dist
        cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = qc + tag + ".png"; bpy.ops.render.render(write_still=True)
