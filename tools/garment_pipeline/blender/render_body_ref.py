"""Stage 1a: front ortho render of the CC5 body (T-pose) as a mannequin reference for the concept image."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from common import *
A = args(); reset()
objs = import_obj(A["body"], use_split_groups=True)
keep = {"CC_Base_Body"}
for o in objs:
    if not any(o.name.startswith(k) for k in keep): bpy.data.objects.remove(o)
body = [o for o in bpy.data.objects if o.type == "MESH"]
m = flat_mat("Mannequin", (0.38, 0.36, 0.35), 0.6)
for o in body: o.data.materials.clear(); o.data.materials.append(m)
lo, hi = bbox(body)
H = hi.z - lo.z; W = hi.x - lo.x
info = {"bbox_lo": list(lo), "bbox_hi": list(hi), "height": H, "arm_span": W}
# frame: full arm span, from mid-thigh to above head -> square
top = hi.z + 0.03 * H; bottom = lo.z + 0.42 * H
size = max(W * 1.06, top - bottom)
c = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (top + bottom) / 2)
setup_render((1024, 1024), (0.85, 0.85, 0.85)); sun(energy=1.6); sun((0.9, -0.3, -2.6), 0.6)
ortho_camera(c, size)
info.update(cam_center=list(c), cam_scale=size, res=1024)
render(A["out"])
json.dump(info, open(os.path.splitext(A["out"])[0] + ".json", "w"), indent=1)
print("REF", json.dumps(info))
