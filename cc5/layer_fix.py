# Shirt vs trousers poking through each other — fixed in one go (no guessing, no UI clicks).
#   mode "out": shirt hangs OUTSIDE the trousers/skirt      mode "in": shirt TUCKED IN (trousers pushed outside the shirt)
# Use cc5\shirt_out.py / cc5\shirt_in.py from Script > Load Python, or build.py calls fix() when job.json has "layer".
# How: both garments -> OBJ (current pose, Z-up, cm) -> Blender headless blender\layer_fix_obj.py pushes only the
# vertices that are inside the other garment past its outermost layer (8 cm fade) -> ReplaceMesh (keeps weights/UV/material).
import json, os, subprocess, sys, time, traceback
import RLPy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

SHOE = ("flop", "sandal", "sandle", "shoe", "boot")


def fix(av, d, mode, log):
    clothes = {o.GetName(): o for o in av.GetClothes()}
    upper = [n for n in open(os.path.join(d, "upper.txt"), encoding="utf-8").read().split("\n") if n in clothes][0]
    lower = [n for n in clothes if n != upper and not any(s in n.lower() for s in SHOE)][0]
    outer, inner = (upper, lower) if mode == "out" else (lower, upper)
    log.append("layer %s: outer=%s inner=%s" % (mode, outer, inner))
    work = os.path.join(d, "layer_fix")
    os.makedirs(work, exist_ok=True)
    f = {k: os.path.join(work, k + ".obj") for k in ("outer", "inner", "fixed")}
    for p in f.values():
        if os.path.exists(p):
            os.remove(p)
    RLPy.RFileIO.ExportObjFile(clothes[outer], f["outer"], RLPy.EExport3DFileOption__None)
    RLPy.RFileIO.ExportObjFile(clothes[inner], f["inner"], RLPy.EExport3DFileOption__None)
    t = time.time()
    r = subprocess.run([kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "layer_fix_obj.py"), "--",
                        f["outer"], f["inner"], f["fixed"]], capture_output=True, text=True, timeout=900)
    log += [l for l in r.stdout.splitlines() if l.startswith(("MOVED", "WROTE"))]
    log.append("blender %.0fs rc=%s" % (time.time() - t, r.returncode))
    if not os.path.exists(f["fixed"]):
        raise RuntimeError("blender failed:\n" + r.stdout[-1500:] + r.stderr[-1500:])
    clothes[outer].GetMeshes()[0].ReplaceMesh(f["fixed"], RLPy.EReplaceMeshOption_ZUp, False)


def main(mode):
    """Run on the current job (first line of batch.txt): load its project, fix, render, save."""
    d = kit.current_job()
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
    log = []
    try:
        proj = os.path.join(d, name + ".ccProject")
        if os.path.exists(proj):
            RLPy.RFileIO.LoadFile(proj)
        av = RLPy.RScene.GetAvatars()[0]
        fix(av, d, mode, log)
        RLPy.RScene.SelectObject(av)
        RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
        RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
        s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
        RLPy.RFileIO.SaveFile(av, s, proj)
        log.append("OK saved")
    except Exception:
        log.append("FAIL\n" + traceback.format_exc())
    open(os.path.join(d, "layer_fix.txt"), "w", encoding="utf-8").write("\n".join(log))
