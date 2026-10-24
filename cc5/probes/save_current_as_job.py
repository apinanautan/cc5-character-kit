# Save what is open in CC5 (A-pose) as the job's character project.
import json, os, sys, RLPy
sys.path.insert(0, r"C:\Users\Apinan\Documents\CC5 Characters"); import kit
d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\A-Pose.rlPose")
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
BRIDGE_RESULT = "saved %s clothes=%s" % (name, [c.GetName() for c in av.GetClothes()])
