# Bridge: save the upper / lower garments of the open avatar as .ccCloth files (to move one character's outfit onto another).
#   python tools\cc5.py run cc5\probes\save_cloth.py out=<folder> prefix=<name>
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
os.makedirs(A["out"], exist_ok=True)
av = RLPy.RScene.GetAvatars()[0]
res = []
for kind in ("Upper", "Lower"):
    s = RLPy.RSaveFileSetting()
    s.SetSaveType(getattr(RLPy, "ESaveFileType_" + kind))
    RLPy.RScene.SelectObject(av)
    r = RLPy.RFileIO.SaveFile(av, s, os.path.join(A["out"], A.get("prefix", "c") + "_" + kind + ".ccCloth"))
    res.append("%s:%s" % (kind, r.IsError() if hasattr(r, "IsError") else r))
BRIDGE_RESULT = " ".join(res)
