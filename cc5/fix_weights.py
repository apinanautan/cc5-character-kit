# Bridge: re-skin clothes from the body (CC5 "Transfer Skin Weights") so sleeves follow the arms
# instead of being glued to the torso, then check in T-pose and save.
#   python tools\cc5.py run cc5\fix_weights.py job=krong_elder_f [cloth=collar] [template=Default] [save=1]
# cloth = part of the garment name (default: the top from upper.txt). Renders <job>\weights_before.png and weights_after.png (T-pose) to compare.
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(d, name + ".ccProject")
TPOSE = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\T-Pose.rlPose"
log = []


def load():
    RLPy.RFileIO.LoadFile(proj)
    return RLPy.RScene.GetAvatars()[0]


def tpose_render(av, png):
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(TPOSE)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(png)


av = load()
tpose_render(av, os.path.join(d, "weights_before.png"))
av = load()
up = os.path.join(d, "upper.txt")  # default: the top garment
names = [A["cloth"]] if A.get("cloth") else open(up, encoding="utf-8").read().splitlines() if os.path.exists(up) else [""]
for c in av.GetClothes():
    if any(n.lower() in c.GetName().lower() for n in names):
        r = c.TransferSkinWeight(A.get("template", "Default"))
        log.append("transfer %s -> %s" % (c.GetName(), "error" if r.IsError() else "ok"))
if A.get("save") == "1":
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, proj)
    log.append("saved")
tpose_render(av, os.path.join(d, "weights_after.png"))
BRIDGE_RESULT = "\n".join(log)
