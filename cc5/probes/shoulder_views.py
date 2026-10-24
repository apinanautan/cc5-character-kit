import os, RLPy
P = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av); RLPy.RFileIO.LoadFile(os.path.join(P, "A-Pose.rlPose"))
out = []
for tag, loc in (("l", RLPy.ECameraLocationType_Left), ("r", RLPy.ECameraLocationType_Right), ("f", RLPy.ECameraLocationType_Front)):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(loc)
    p = os.path.join(os.environ["TEMP"], "sh_%s.png" % tag); RLPy.RGlobal.RenderImage(p); out.append(p)
BRIDGE_RESULT = "\n".join(out)
