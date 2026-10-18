# Run inside CC5: list the body shaping sliders (for thin / pregnant) -> cc5_jobs\morph_probe.txt
import os
import RLPy
out = []
av = RLPy.RScene.GetAvatars()[0]
c = av.GetAvatarShapingComponent()
out.append("shaping: " + ", ".join(n for n in dir(c) if not n.startswith("_")))
for lister in ("GetShapingMorphIDs", "GetShapingMorphNames", "GetShapingMorphDisplayNames"):
    if hasattr(c, lister):
        for arg in ((), ("",)):
            try:
                names = list(getattr(c, lister)(*arg))
                out.append("%s%r (%d):\n%s" % (lister, arg, len(names), "\n".join(names)))
                break
            except Exception as e:
                out.append("%s%r err %r" % (lister, arg, e))
open(os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "morph_probe.txt"), "w", encoding="utf-8").write("\n".join(out))
