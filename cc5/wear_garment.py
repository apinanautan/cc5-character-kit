# Bridge: put a fitted AI garment (OBJ from blender/fit_garment.py, made in T-pose) on a job's character.
#   python tools\cc5.py run cc5\wear_garment.py job=<job> obj=<fitted.obj> [remove=top|none] [template=Default] [save=<name>]
# T-pose -> LoadAccessoryWithTransferSkinWeight (arms and torso far apart = clean weights) -> back to A-pose ->
# renders <job>\garment_T.png (T-pose) and garment_A.png (A-pose), and saves <save>.ccProject in the job folder
# (never overwrites the character's own project).
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
POSES = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
log = []
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
if A.get("remove", "top") == "top":  # take off the old top (upper.txt) so only the new one shows
    up = os.path.join(d, "upper.txt")
    names = open(up, encoding="utf-8").read().splitlines() if os.path.exists(up) else []
    for c in av.GetClothes():
        if c.GetName() in names:
            RLPy.RScene.RemoveObject(c)
            log.append("removed " + c.GetName())
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, "T-Pose.rlPose"))
before = set(o.GetName() for o in av.GetAccessories())
r = av.LoadAccessoryWithTransferSkinWeight(A["obj"], A.get("template", "Default"))
new = [o.GetName() for o in av.GetAccessories() if o.GetName() not in before]
log.append("load %s -> %s, new accessories %s" % (os.path.basename(A["obj"]), "error" if r.IsError() else "ok", new))


def shot(png):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(d, png))


shot("garment_T.png")
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, "A-Pose.rlPose"))
shot("garment_A.png")
if A.get("save"):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, os.path.join(d, A["save"] + ".ccProject"))
    log.append("saved " + A["save"])
BRIDGE_RESULT = "\n".join(log)
