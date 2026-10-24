# Bridge: save every garment of a finished character (.iAvatar / .ccProject) as its own file, to reuse on others.
#   python tools\cc5.py run cc5\extract_outfit.py path=<character file> out=<folder>
# Shoes -> .ccShoes; the others -> .ccCloth (saved as Upper; CC5 keeps the garment's own fit/weights).
import os
import RLPy

A = BRIDGE_ARGS  # noqa: F821
os.makedirs(A["out"], exist_ok=True)
RLPy.RFileIO.LoadFile(A["path"])
av = RLPy.RScene.GetAvatars()[0]
log = []
SHOE = ("shoe", "flop", "sandal", "boot")
for c in av.GetClothes():
    n = c.GetName()
    shoe = any(k in n.lower() for k in SHOE)
    s = RLPy.RSaveFileSetting()
    s.SetSaveType(RLPy.ESaveFileType_Shoes if shoe else RLPy.ESaveFileType_Upper)
    p = os.path.join(A["out"], n + (".ccShoes" if shoe else ".ccCloth"))
    r = RLPy.RFileIO.SaveFile(c, s, p)
    log.append("%s -> %s %s" % (n, os.path.basename(p), "ok" if os.path.exists(p) else "FAILED %r" % r))
BRIDGE_RESULT = "\n".join(log)
