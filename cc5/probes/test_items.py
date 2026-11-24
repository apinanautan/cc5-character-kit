# Wear library cloth items one at a time on the base Neutral body and render each (for a contact sheet).
# One CC5 run = one batch; progress is written after every item so a hang loses only that item.
#   tools\cc5.py run cc5\probes\test_items.py list=<cand.json> start=0 count=12 out=<dir>
import json, os, time
import RLPy
A = BRIDGE_ARGS  # noqa: F821
items = json.load(open(A["list"], encoding="utf-8"))[int(A["start"]):int(A["start"]) + int(A["count"])]
os.makedirs(A["out"], exist_ok=True)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Actor\Character\Base\Neutral_M.ccAvatar")
av = RLPy.RScene.GetAvatars()[0]
log = open(os.path.join(A["out"], "result.txt"), "a", encoding="utf-8")
for n, it in enumerate(items, int(A["start"])):
    if it.get("skip"):
        log.write("%03d\tSKIP\t%s\n" % (n, it["path"])); log.flush(); continue
    for o in list(av.GetClothes()) + list(av.GetAccessories()):
        RLPy.RScene.RemoveObject(o)
    t = time.time()
    line = "%03d\tFAIL\t%s" % (n, it["path"])
    try:
        RLPy.RScene.SelectObject(av)
        RLPy.RFileIO.LoadFile(it["path"])
        names = [c.GetName() for c in av.GetClothes()]
        RLPy.RScene.SelectObject(av)
        RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
        RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%03d.png" % n))
        line = "%03d\t%d\t%.0fs\t%s\t%s" % (n, len(names), time.time() - t, names, it["path"])
    except Exception as e:
        line += "\t" + str(e)[:80]
    log.write(line + "\n"); log.flush()
BRIDGE_RESULT = "done %d" % len(items)
