# Bridge: render the avatar that is open (front camera) to A["out"]; pose=A-Pose (default) sets the standard pose first.
#   python tools\cc5.py run cc5\render_front.py out=<png> [pose=A-Pose]
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
if A.get("pose", "A-Pose") != "none":
    RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\%s.rlPose" % A.get("pose", "A-Pose"))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(getattr(RLPy, "ECameraLocationType_" + A.get("cam", "Front")))
RLPy.RGlobal.RenderImage(A["out"])
BRIDGE_RESULT = "wearing %s" % [c.GetName() for c in av.GetClothes()]
