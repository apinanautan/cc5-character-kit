# Run inside iClone 8: one top-view render framed on the house -> ic8_jobs\look_top.png
import os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
house = RLPy.RScene.FindObject(RLPy.EObjectType_Prop, "Hut")
RLPy.RScene.SelectObject(house)
cam = RLPy.RScene.GetCurrentCamera()
cam.SetCameraLocation(RLPy.ECameraLocationType_Top)
cam.SetCameraLocation(RLPy.ECameraLocationType_Focus)
RLPy.RGlobal.RenderImage(os.path.join(J, "look_top.png"))
