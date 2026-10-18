# CC5 > Script > Load Python: faces per garment of the CURRENT avatar + front render -> cc5_jobs\count_current.txt/.png
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

av = RLPy.RScene.GetAvatars()[0]
lines = []
for kind, objs in (("cloth", av.GetClothes()), ("hair", av.GetHairs()), ("acc", av.GetAccessories())):
    for o in objs:
        lines.append("%s %s %d" % (kind, o.GetName(), sum(m.GetFacesCount() for m in o.GetMeshes())))
lines.append("avatar total %d" % sum(m.GetFacesCount() for m in av.GetMeshes()))
open(os.path.join(kit.JOBS, "count_current.txt"), "w", encoding="utf-8").write("\n".join(lines))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(kit.JOBS, "count_current.png"))
