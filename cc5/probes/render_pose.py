# Render the loaded avatar in a calibration pose (pose=T-Pose|A-Pose) to out=<png>
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration", A.get("pose", "T-Pose") + ".rlPose"))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
for _ in range(2):
    RLPy.RGlobal.RenderImage(A["out"])
