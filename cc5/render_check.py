# Run inside CC5: render front + left of the current avatar -> cc5_jobs\check_front.png / check_left.png
import os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
cam = RLPy.RScene.GetCurrentCamera()
for loc, n in ((RLPy.ECameraLocationType_Left, "check_left.png"), (RLPy.ECameraLocationType_Front, "check_front.png")):
    cam.SetCameraLocation(loc)
    RLPy.RGlobal.RenderImage(os.path.join(J, n))
