# Bridge: in the avatar already open: delete the current shoes (name contains flop/shoe/sandal/boot) and load a .ccShoes.
#   python tools\cc5.py run cc5\swap_shoes.py path=<x.ccShoes>
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
gone = []
for c in list(av.GetClothes()):
    if any(k in c.GetName().lower() for k in ("flop", "sandal", "sandle", "shoe", "boot")):
        gone.append(c.GetName()); RLPy.RScene.RemoveObject(c)
RLPy.RScene.SelectObject(av)
r = RLPy.RFileIO.LoadFile(A["path"])
BRIDGE_RESULT = "removed %s; clothes now %s" % (gone, [c.GetName() for c in av.GetClothes()])
