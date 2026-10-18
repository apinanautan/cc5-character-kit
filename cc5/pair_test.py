# Run inside CC5: for each (top, bottom) pair in cc5_jobs\pair_test.json, strip clothes, load bottom then top,
# record whether both stay on -> cc5_jobs\pair_test_result.txt  (no render, ~10 s per pair)
import json, os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
cfg = json.load(open(os.path.join(J, "pair_test.json"), encoding="utf-8"))
av = RLPy.RScene.GetAvatars()[0]
out = []
for top in cfg["tops"]:
    for bottom in cfg["bottoms"]:
        for o in list(av.GetClothes()):
            RLPy.RScene.RemoveObject(o)
        names = []
        for f in (bottom, top):
            before = set(o.GetName() for o in av.GetClothes())
            RLPy.RScene.SelectObject(av)
            RLPy.RFileIO.LoadFile(f)
            names.append([o.GetName() for o in av.GetClothes() if o.GetName() not in before])
        now = set(o.GetName() for o in av.GetClothes())
        ok = all(n and all(x in now for x in n) for n in names)
        out.append("%s\t%s\t%s" % ("OK" if ok else "CLASH", os.path.basename(os.path.dirname(top)) + "/" + os.path.basename(top),
                                    os.path.basename(os.path.dirname(bottom)) + "/" + os.path.basename(bottom)))
        open(os.path.join(J, "pair_test_result.txt"), "w", encoding="utf-8").write("\n".join(out))
out.append("DONE")
open(os.path.join(J, "pair_test_result.txt"), "w", encoding="utf-8").write("\n".join(out))
