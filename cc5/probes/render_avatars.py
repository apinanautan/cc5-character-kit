# Open each .iAvatar from a list in CC5 (one after another), A-pose, front camera, same light -> <out>/<i>.png   (nothing is saved)
#   tools\cc5.py run cc5\probes\render_avatars.py list=<list.json> start=0 count=5 out=<dir>
import json, os, time
import RLPy
A = BRIDGE_ARGS  # noqa: F821
items = json.load(open(A["list"], encoding="utf-8"))[int(A["start"]):int(A["start"]) + int(A["count"])]
os.makedirs(A["out"], exist_ok=True)
log = open(os.path.join(A["out"], "result.txt"), "a", encoding="utf-8")
POSE = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\A-Pose.rlPose"
for it in items:
    t = time.time(); line = "%03d\tFAIL\t%s" % (it["i"], it["path"])
    try:
        for a in list(RLPy.RScene.GetAvatars()):
            RLPy.RScene.RemoveObject(a)
        for p in list(RLPy.RScene.GetProps()):
            if p.GetName() != "Shadow Catcher":
                RLPy.RScene.RemoveObject(p)
        RLPy.RFileIO.LoadFile(it["path"])
        av = RLPy.RScene.GetAvatars()[0]
        RLPy.RScene.SelectObject(av)
        RLPy.RFileIO.LoadFile(POSE)
        RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
        RLPy.RGlobal.RenderImage(os.path.join(A["out"], "%03d.png" % it["i"]))
        line = "%03d\tOK\t%.0fs\t%s" % (it["i"], time.time() - t, it["name"])
    except Exception as e:
        line += "\t" + str(e)[:80]
    log.write(line + "\n"); log.flush()
BRIDGE_RESULT = "done %d" % len(items)
