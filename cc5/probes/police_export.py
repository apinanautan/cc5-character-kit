# python tools/cc5.py run cc5/probes/police_export.py find=<substring of file name> root=<folder> out=<folder>
# Load a finished character found under root, put it in T-pose, render it, and export every garment / accessory as OBJ.
import os
import RLPy

A = BRIDGE_ARGS  # noqa: F821
path = None
for dp, dn, fn in os.walk(A["root"]):
    for f in fn:
        if A["find"].lower() in f.lower() and f.lower().endswith(".iavatar"):
            path = os.path.join(dp, f)
os.makedirs(A["out"], exist_ok=True)
log = ["path: %s" % path]
RLPy.RFileIO.LoadFile(path)
av = RLPy.RScene.GetAvatars()[0]
POSES = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, A.get("pose", "T-Pose") + ".rlPose"))
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(A["out"], "src_T.png"))
for kind, objs in (("cloth", av.GetClothes()), ("acc", av.GetAccessories())):
    for i, o in enumerate(objs):
        n = o.GetName()
        dest = os.path.join(A["out"], "%s%d_%s.obj" % (kind, i, "".join(ch if ch.isalnum() else "_" for ch in n)))
        try:
            r = RLPy.RFileIO.ExportObjFile(o, dest, RLPy.EExport3DFileOption__None)
            log.append("%s %s -> %s %s" % (kind, n, os.path.basename(dest), os.path.getsize(dest) if os.path.exists(dest) else "MISSING"))
        except Exception as e:
            log.append("%s %s EXC %s" % (kind, n, e))
BRIDGE_RESULT = "\n".join(log)
