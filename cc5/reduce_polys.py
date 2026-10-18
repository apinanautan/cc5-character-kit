# CC5 > Script > Load Python: lighten the current job's heavy garments (first line of batch.txt).
# Every cloth over LIMIT faces -> OBJ (current pose) -> Blender decimate (blender\decimate_obj.py, UVs kept)
# -> ReplaceMesh -> render <name>.png, save project. Log: <job>\reduce.txt (faces before -> after per garment).
import json, os, subprocess, sys, traceback
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

LIMIT = 20000     # garments above this are reduced
TARGET = 12000    # tops / shoes
TARGET_LONG = 15000  # long skirts / trousers / dresses (more cloth area)

d = kit.current_job()
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
work = os.path.join(d, "reduce")
os.makedirs(work, exist_ok=True)
log = []
try:
    proj = os.path.join(d, name + ".ccProject")
    RLPy.RFileIO.LoadFile(proj)
    av = RLPy.RScene.GetAvatars()[0]
    for cl in av.GetClothes():
        for mesh in cl.GetMeshes():
            n = mesh.GetFacesCount()
            if n <= LIMIT:
                continue
            ys = [v.z for v in mesh.GetVertices(True)]  # world height (Z up): long garment = covers >60 cm
            target = TARGET_LONG if (max(ys) - min(ys)) > 60 else TARGET
            src, dst = os.path.join(work, cl.GetName() + ".obj"), os.path.join(work, cl.GetName() + "_low.obj")
            RLPy.RFileIO.ExportObjFile(cl, src, RLPy.EExport3DFileOption__None)
            r = subprocess.run([kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "decimate_obj.py"), "--",
                                src, dst, str(target)], capture_output=True, text=True, timeout=900)
            if not os.path.exists(dst):
                log.append("FAIL blender %s\n%s" % (cl.GetName(), r.stdout[-800:] + r.stderr[-800:]))
                continue
            st = mesh.ReplaceMesh(dst, RLPy.EReplaceMeshOption_ZUp, True)
            log.append("%s: %d -> %d faces (%s)" % (cl.GetName(), n, mesh.GetFacesCount(), st))
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, proj)
    log.append("OK saved")
except Exception:
    log.append("FAIL\n" + traceback.format_exc())
open(os.path.join(d, "reduce.txt"), "w", encoding="utf-8").write("\n".join(log))
