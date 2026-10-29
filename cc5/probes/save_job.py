# Save the loaded avatar as the job's project (A-pose render first): tools\cc5.py run cc5\probes\save_job.py job=<dir>
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration", "A-Pose.rlPose"))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
for _ in range(2):
    RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
BRIDGE_RESULT = "saved %s clothes=%s" % (name, [c.GetName() for c in av.GetClothes()])
