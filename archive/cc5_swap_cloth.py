# Run inside CC5: replace cloth whose name contains swap.json["old"] with FBX swap.json["fbx"], then render swap_test.png
import json, os, traceback, RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
cfg = json.load(open(os.path.join(J, "swap.json"), encoding="utf-8"))
av = RLPy.RScene.GetAvatars()[0]; log = []
try:
    before = set(o.GetName() for o in av.GetClothes())
    for o in list(av.GetClothes()):
        if cfg["old"] in o.GetName():
            RLPy.RScene.RemoveObject(o); log.append("removed " + o.GetName())
    failed = RLPy.RStringVector() if hasattr(RLPy, "RStringVector") else []
    r = RLPy.RFileIO.LoadClotheFromFbx(av, cfg["fbx"], failed)
    log.append("load %r failed=%r now=%r" % (r, list(failed), [o.GetName() for o in av.GetClothes()]))
except Exception:
    log.append(traceback.format_exc())
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(J, "swap_test.png"))
open(os.path.join(J, "swap_log.txt"), "w", encoding="utf-8").write("\n".join(log))
