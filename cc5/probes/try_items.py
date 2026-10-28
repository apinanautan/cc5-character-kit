# Try library items one by one on the loaded avatar: strip clothes, load item, render <out>\<n>.png, report what loaded.
#   tools\cc5.py run cc5\probes\try_items.py "items=a.ccCloth;b.ccCloth" out=C:\...\dir [project=X.ccProject]
import os, time
import RLPy
A = BRIDGE_ARGS  # noqa: F821
if A.get("project"):
    RLPy.RFileIO.LoadFile(A["project"])
av = RLPy.RScene.GetAvatars()[0]
os.makedirs(A["out"], exist_ok=True)
res = []
for n, item in enumerate(A["items"].split(";")):
    for o in list(av.GetClothes()):
        RLPy.RScene.RemoveObject(o)
    RLPy.RScene.SelectObject(av)
    t = time.time()
    for part in item.split("+"):  # "a+b" = wear both (bottom first)
        RLPy.RScene.SelectObject(av)
        RLPy.RFileIO.LoadFile(part)
    names = [o.GetName() for o in av.GetClothes()]
    acc = [o.GetName() for o in av.GetAccessories()]
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    for _ in range(2):
        RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%02d.png" % (n + 1)))
    res.append("%02d %.0fs clothes=%s acc=%s %s" % (n + 1, time.time() - t, names, acc, " + ".join(os.path.basename(p) for p in item.split("+"))))
open(os.path.join(A["out"], "result.txt"), "w", encoding="utf-8").write("\n".join(res))
BRIDGE_RESULT = "\n".join(res)
