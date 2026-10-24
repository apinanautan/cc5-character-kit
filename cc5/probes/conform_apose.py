# A-pose, then Conform (Calculate Collision) the named cloth so skin no longer pokes through; render A + T.
import os, RLPy
A = BRIDGE_ARGS  # noqa: F821
P = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
av = RLPy.RScene.GetAvatars()[0]
out = os.environ["TEMP"]
def shot(png):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(out, png))
RLPy.RScene.SelectObject(av); RLPy.RFileIO.LoadFile(os.path.join(P, "A-Pose.rlPose"))
shot("conf_before_A.png")
log = []
for c in av.GetClothes():
    if c.GetName() in A["cloth"].split(","):
        for k, v in (("Iteration", float(A.get("it", 5))), ("Margin", float(A.get("margin", 0.5))), ("IncreaseSize", float(A.get("inc", 0.3)))):
            c.SetClothConformValue(k, v)
        r = c.CalculateCollision()
        log.append("conform %s -> %s" % (c.GetName(), r))
shot("conf_after_A.png")
RLPy.RScene.SelectObject(av); RLPy.RFileIO.LoadFile(os.path.join(P, "T-Pose.rlPose"))
shot("conf_after_T.png")
BRIDGE_RESULT = "\n".join(log)
