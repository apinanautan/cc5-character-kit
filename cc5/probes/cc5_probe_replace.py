# Run inside CC5: export the upper garment as OBJ and ReplaceMesh it with itself (round-trip test) -> replace_probe.txt + replace_test.png
import os, traceback
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
out = []
try:
    d = open(os.path.join(J, "batch_krong.txt"), encoding="utf-8").read().split("\n")[0].strip()
    upper = open(os.path.join(d, "upper.txt"), encoding="utf-8").read().split("\n")[0]
    av = RLPy.RScene.GetAvatars()[0]
    out.append("clothes %r upper %r" % ([o.GetName() for o in av.GetClothes()], upper))
    cl = [o for o in av.GetClothes() if o.GetName() == upper][0]
    out.append("meshes %r" % (list(cl.GetMeshNames()),))
    for k in ("Increase Size", "IncreaseSize", "Margin", "Iteration", "Close-fitting", "Smooth"):
        try:
            out.append("conform %s = %r" % (k, cl.GetClothConformValue(k)))
        except Exception as e:
            out.append("conform %s ERR %r" % (k, e))
    p = os.path.join(d, "layer_fix", "upper.obj")
    out.append("export %r" % (RLPy.RFileIO.ExportObjFile(cl, p),))
    mesh = list(cl.GetMeshNames())[0]
    for label, fn in (("av(mesh,obj)", lambda: av.ReplaceMesh(mesh, p)),
                      ("av(mesh,obj,ZUp)", lambda: av.ReplaceMesh(mesh, p, RLPy.EReplaceMeshOption_ZUp))):
        try:
            out.append("%s -> %r" % (label, fn()))
            break
        except Exception as e:
            out.append("%s ERR %r" % (label, e))
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(J, "replace_test.png"))
except Exception:
    out.append(traceback.format_exc())
open(os.path.join(J, "replace_probe.txt"), "w", encoding="utf-8").write("\n".join(out))
