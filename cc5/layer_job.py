# Bridge: shirt in/out fix for any job, then render + save.
#   python tools\cc5.py run cc5\layer_job.py job=krong_somjit_40 mode=out
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, kit, layer_fix
importlib.reload(layer_fix)

d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821
mode = BRIDGE_ARGS.get("mode", "out")  # noqa: F821
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(d, name + ".ccProject")
RLPy.RFileIO.LoadFile(proj)
av = RLPy.RScene.GetAvatars()[0]
log = []
layer_fix.fix(av, d, mode, log)
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, proj)
BRIDGE_RESULT = "\n".join(log)
