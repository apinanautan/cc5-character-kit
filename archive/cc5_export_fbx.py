# Run inside CC5: export each cloth of the current character as OBJ (+ whole avatar FBX) into cc5_jobs\uvtest.
import os, traceback
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "uvtest")
log = []
av = RLPy.RScene.GetAvatars()[0]
for cl in av.GetClothes():
    p = os.path.join(J, cl.GetName() + ".obj")
    try:
        r = RLPy.RFileIO.ExportObjFile(cl, p)
        log.append("obj %s %r %s" % (cl.GetName(), r, os.path.exists(p)))
    except Exception:
        log.append("obj FAIL %s %s" % (cl.GetName(), traceback.format_exc()[-900:]))
try:
    r = RLPy.RFileIO.ExportFbxFile(av, os.path.join(J, "char.fbx"), RLPy.EExportFbxOptions__None,
                                   RLPy.EExportFbxOptions2__None, RLPy.EExportFbxOptions3__None)
    log.append("fbx %r %s" % (r, os.path.exists(os.path.join(J, "char.fbx"))))
except Exception:
    log.append("fbx FAIL " + traceback.format_exc()[-600:])
open(os.path.join(J, "fbx_log.txt"), "w", encoding="utf-8").write("\n".join(log))
