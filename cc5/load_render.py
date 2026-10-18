# Bridge: open a job's saved character, render front view to <job>\check.png, report faces per garment.
#   python tools\cc5.py run cc5\load_render.py job=krong_banphot
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821 (set by the bridge)
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, "check.png"))
BRIDGE_RESULT = "%s rendered -> %s\n" % (name, os.path.join(d, "check.png")) + "\n".join(
    "%s %d faces" % (c.GetName(), sum(m.GetFacesCount() for m in c.GetMeshes())) for c in av.GetClothes())
