# Conform > Calculate Collision on named clothes of the loaded avatar, render + save the job project.
#   tools\cc5.py run cc5\probes\collide_cloth.py job=<job dir> names=a;b [margin=0.4]
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
av = RLPy.RScene.GetAvatars()[0]
done = []
for c in av.GetClothes():
    if c.GetName() in A["names"].split(";"):
        for k, v in (("Iteration", 5.0), ("Margin", float(A.get("margin", 0.4))), ("IncreaseSize", 0.0)):
            c.SetClothConformValue(k, v)
        c.CalculateCollision(); done.append(c.GetName())
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
for _ in range(2):
    RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
BRIDGE_RESULT = "collided %s" % done
