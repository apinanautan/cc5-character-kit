# Garment pipeline stage 0 (inside CC5 via bridge). Never overwrites anything.
# args: source=<character .ccProject>, out=<run dir>, preserve=<path or ''> , upper=<comma names to take off or 'auto'>
# 1) saves the scene that is currently open to a NEW file (so unsaved work is never lost),
# 2) opens the source character, takes off the upper garment(s), T-pose, exports body+remaining clothes OBJ,
# 3) writes body_info.json. The source project on disk is not modified.
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, pose, save_character
A = BRIDGE_ARGS  # noqa
out = A["out"]; os.makedirs(out, exist_ok=True)
log = []
if A.get("preserve"):
    avs = RLPy.RScene.GetAvatars()
    if avs and not os.path.exists(A["preserve"]):
        save_character(avs[0], A["preserve"]); log.append("preserved current scene -> " + A["preserve"])
r = RLPy.RFileIO.LoadFile(A["source"]); settle(1500)
if r.IsError(): raise RuntimeError("cannot open " + A["source"])
av = RLPy.RScene.GetAvatars()[0]
clothes = []
for c in av.GetClothes():
    t = None
    try: t = int(c.GetClothType()) if hasattr(c, "GetClothType") else None
    except Exception: pass
    clothes.append({"name": c.GetName(), "faces": sum(m.GetFacesCount() for m in c.GetMeshes()), "type": t})
names = [n for n in A.get("upper", "").split(",") if n]
removed = []
for c in av.GetClothes():
    if c.GetName() in names:
        RLPy.RScene.RemoveObject(c); removed.append(c.GetName())
pose(av, "T-Pose")
body = os.path.join(out, "body_tpose.obj")
RLPy.RFileIO.ExportObjFile(av, body, RLPy.EExport3DFileOption__None)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front); settle(500)
RLPy.RGlobal.RenderImage(os.path.join(out, "cc5_body_T_front.png"))
info = {"source": A["source"], "clothes": clothes, "removed": removed, "body_obj": body, "log": log}
json.dump(info, open(os.path.join(out, "body_info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
BRIDGE_RESULT = json.dumps(info, ensure_ascii=False)
