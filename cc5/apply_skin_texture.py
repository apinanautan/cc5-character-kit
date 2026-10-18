# CC5 > Script > Load Python: load the current job's project, put a painted arm texture on it, render, save.
# Texture = job.json "skin_arm" (file in data\ or full path), e.g. arm_burn.png made by tools\paint_burn_scar.py.
# Usually not needed by hand: build.py applies "skin_arm" itself.
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

d = kit.current_job()
job = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))
name = job["name"]
tex = job["skin_arm"] if os.path.isabs(job["skin_arm"]) else os.path.join(kit.REPO, "data", job["skin_arm"])
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
av.GetMaterialComponent().LoadImageToTexture("CC_Base_Body", "Std_Skin_Arm", RLPy.EMaterialTextureChannel_Diffuse, tex)
av.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
