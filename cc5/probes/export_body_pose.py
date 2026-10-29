# Export the bare body (no clothes / hair / accessories) of a job in a calibration pose: nothing is saved.
#   tools\cc5.py run cc5\probes\export_body_pose.py job=<dir> pose=A-Pose out=<obj>
import json, os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
for o in list(av.GetClothes()) + list(av.GetHairs()) + list(av.GetAccessories()):
    RLPy.RScene.RemoveObject(o)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration", A.get("pose", "A-Pose") + ".rlPose"))
RLPy.RFileIO.ExportObjFile(av, A["out"], RLPy.EExport3DFileOption__None)
BRIDGE_RESULT = "exported %s" % A["out"]
