# Headless: CC5 soft-cloth PHYSICS WEIGHT MAP for one of our garments (grey image on the garment's UVs).
# Black = sticks to the skin, white = fully simulated. We keep it light: only the hem (and for tops a touch under the arms).
#   blender -b -P make_weightmap.py -- <garment.obj Y-up> <out.png> <kind=top|skirt> [size=1024] [hem=0.45] [arm=0.25]
#                                     [hem_band=0.12] [buttons_uv.json]
# hem / arm = grey value (0..1) at the very edge; hem_band = fraction of garment height that moves (from the hem up).
# Buttons (separate small pieces + their UV square) are forced black so they never fall off the cloth.
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--") + 1:]
g_p, out_p, KIND = a[0], a[1], a[2]
kw = dict(x.split("=") for x in a[3:] if "=" in x)
files = [x for x in a[3:] if "=" not in x]
SIZE = int(kw.get("size", 1024)); HEM = float(kw.get("hem", 0.45)); ARM = float(kw.get("arm", 0.25))
BAND = float(kw.get("hem_band", 0.12 if KIND == "top" else 0.45))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.wm.obj_import(filepath=g_p, forward_axis="NEGATIVE_Z", up_axis="Y")
gar = [o for o in sc.objects if o.type == "MESH"][0]; gar.data.transform(gar.matrix_world); gar.matrix_world = Matrix.Identity(4)
me = gar.data; V = [v.co.copy() for v in me.vertices]; n = len(V)
zmin = min(p.z for p in V); zmax = max(p.z for p in V); Hh = zmax - zmin

# connected pieces: everything < 5 % of the vertices is a button -> weight 0
nb = [[] for _ in range(n)]
for e in me.edges: i, j = e.vertices; nb[i].append(j); nb[j].append(i)
small = [False] * n; seen = [False] * n
for s0 in range(n):
    if seen[s0]: continue
    comp, st = [], [s0]; seen[s0] = True
    while st:
        i = st.pop(); comp.append(i)
        for j in nb[i]:
            if not seen[j]: seen[j] = True; st.append(j)
    if len(comp) < 0.05 * n:
        for i in comp: small[i] = True


def ss(x):  # smoothstep 0..1
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


w = [0.0] * n
for i, p in enumerate(V):
    t = (p.z - zmin) / (BAND * Hh)                 # 0 at hem, 1 at top of the moving band
    w[i] = HEM * ss(1 - t) ** 1.5
if KIND == "top" and ARM > 0:
    # armpit = where the sleeve underside meets the torso side. torso half-width from the lower body part of the top.
    low = [p for p in V if p.z < zmin + 0.35 * Hh]
    xc = (max(p.x for p in low) + min(p.x for p in low)) / 2
    xt = max(abs(p.x - xc) for p in low)
    for sgn in (1, -1):
        sleeve = [p for p in V if sgn * (p.x - xc) > xt * 1.15]
        if not sleeve: continue
        za = min(p.z for p in sleeve)
        ap = Vector((xc + sgn * xt, sum(p.y for p in sleeve) / len(sleeve), za))
        print("ARMPIT", sgn, [round(c, 1) for c in ap])
        for i, p in enumerate(V):
            d = (p - ap).length
            w[i] = max(w[i], ARM * math.exp(-(d / 4.0) ** 2))
for i in range(n):
    if small[i]: w[i] = 0.0
print("WEIGHT max", round(max(w), 3), "verts>0.05", sum(x > 0.05 for x in w), "/", n)

# bake per-vertex weight to the UV image
attr = me.color_attributes.new("w", "FLOAT_COLOR", "POINT")
for i, x in enumerate(w): attr.data[i].color = (x, x, x, 1)
mat = bpy.data.materials.new("w"); mat.use_nodes = True; me.materials.clear(); me.materials.append(mat)
nt = mat.node_tree; L = nt.links
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "w"
emi = nt.nodes.new("ShaderNodeEmission"); L.new(at.outputs["Color"], emi.inputs["Color"])
out = next(nd for nd in nt.nodes if nd.type == "OUTPUT_MATERIAL"); L.new(emi.outputs["Emission"], out.inputs["Surface"])
img = bpy.data.images.new("wmap", SIZE, SIZE, float_buffer=True); img.colorspace_settings.name = "Non-Color"
tg = nt.nodes.new("ShaderNodeTexImage"); tg.image = img; nt.nodes.active = tg
try: sc.render.engine = "CYCLES"
except TypeError: pass
sc.cycles.samples = 1; sc.render.bake.margin = 8
try:
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    bpy.context.preferences.addons["cycles"].preferences.get_devices(); sc.cycles.device = "GPU"
except Exception: pass
bpy.context.view_layer.objects.active = gar; gar.select_set(True)
bpy.ops.object.bake(type="EMIT")
px = np.array(img.pixels[:], np.float32).reshape(SIZE, SIZE, 4)
for f in files:                                   # button UV square -> black
    bj = json.load(open(f)); g = bj["grid"] / 64
    y0, x0, S = int(bj["cell"][0] / 64 * SIZE), int(bj["cell"][1] / 64 * SIZE), int(g * SIZE)
    px[y0:y0 + S, x0:x0 + S, :3] = 0
px[..., 3] = 1
img.pixels[:] = px.ravel()
img.file_format = "PNG"; img.filepath_raw = out_p
sc.view_settings.view_transform = "Standard"
img.save()
print("WROTE", out_p)
