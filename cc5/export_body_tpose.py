# Bridge: put a job's character in T-pose and export its naked body as OBJ (cm, Z-up) for fitting a new garment.
#   python tools\cc5.py run cc5\export_body_tpose.py job=<job> [out=<path.obj>]
# Nothing is saved: the project on disk keeps its clothes and pose.
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
for o in list(av.GetClothes()) + list(av.GetHairs()) + list(av.GetAccessories()):
    RLPy.RScene.RemoveObject(o)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\T-Pose.rlPose")
out = A.get("out") or os.path.join(d, "body_tpose.obj")
RLPy.RFileIO.ExportObjFile(av, out, RLPy.EExport3DFileOption__None)
BRIDGE_RESULT = "exported %s (%d bytes)" % (out, os.path.getsize(out) if os.path.exists(out) else -1)
