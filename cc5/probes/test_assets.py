# Like test_items.py but for the other kinds of asset, on the Neutral base body, one item at a time, front render per item.
#   tools\cc5.py run cc5\probes\test_assets.py list=<cand.json> start=0 count=10 out=<dir> kind=acc|hair|prop
# acc: accessory on the avatar | hair: hair file on the avatar (bald) | prop: prop loaded into the scene next to the avatar
import json, os, time
import RLPy
A = BRIDGE_ARGS  # noqa: F821
kind = A.get("kind", "acc")
items = json.load(open(A["list"], encoding="utf-8"))[int(A["start"]):int(A["start"]) + int(A["count"])]
os.makedirs(A["out"], exist_ok=True)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Actor\Character\Base\Neutral_M.ccAvatar")
av = RLPy.RScene.GetAvatars()[0]
log = open(os.path.join(A["out"], "result.txt"), "a", encoding="utf-8")


def clear():
    for o in list(av.GetClothes()) + list(av.GetAccessories()) + list(av.GetHairs()):
        RLPy.RScene.RemoveObject(o)
    for p in list(RLPy.RScene.GetProps()):
        if p.GetName() != "Shadow Catcher":
            RLPy.RScene.RemoveObject(p)


for n, it in enumerate(items, int(A["start"])):
    clear()
    t = time.time()
    line = "%03d\tFAIL\t%s" % (n, it["path"])
    try:
        RLPy.RScene.SelectObject(av)
        r = RLPy.RFileIO.LoadFile(it["path"])
        names = [o.GetName() for o in list(av.GetAccessories()) + list(av.GetHairs()) + list(RLPy.RScene.GetProps()) if o.GetName() != "Shadow Catcher"]
        RLPy.RScene.SelectObject(av)
        if kind == "hair":   # head close-up (Face camera)
            RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Face)
            RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%03d.png" % n))
        else:
            RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
            RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%03d.png" % n))
        line = "%03d\t%d\t%.0fs\t%s\t%s" % (n, len(names), time.time() - t, names, it["path"])
    except Exception as e:
        line += "\t" + str(e)[:80]
    log.write(line + "\n"); log.flush()
BRIDGE_RESULT = "done %d" % len(items)
