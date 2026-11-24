# python tools\cc5.py run cc5\probes\pose_render.py pose=A-Pose out=<png>   (open avatar: set calibration pose, render front)
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration" + "\\" + A.get("pose", "A-Pose") + ".rlPose")
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(A["out"])
BRIDGE_RESULT = "ok"
