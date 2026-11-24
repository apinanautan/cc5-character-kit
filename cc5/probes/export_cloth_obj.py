# Bridge: export every non-shoe garment of the open avatar as an OBJ (+mtl/textures) at A-pose, to move one character's outfit onto another.
#   python tools\cc5.py run cc5\probes\export_cloth_obj.py out=<folder>
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
os.makedirs(A["out"], exist_ok=True)
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\A-Pose.rlPose")
res = []
for c in av.GetClothes():
    nm = c.GetName()
    if any(k in nm.lower() for k in ("shoe", "flop", "sandal")):
        continue
    p = os.path.join(A["out"], nm + ".obj")
    for args in ((c, p), (p, c), (p, [c])):
        try:
            r = RLPy.RFileIO.ExportObjFile(*args)
            res.append("%s %s ok:%s" % (nm, [type(a).__name__ for a in args], r))
            break
        except Exception as e:
            res.append("%s %s ERR %s" % (nm, [type(a).__name__ for a in args], str(e)[:70]))
BRIDGE_RESULT = " | ".join(res)
