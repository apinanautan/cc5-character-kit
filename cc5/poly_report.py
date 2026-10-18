# CC5 > Script > Load Python: polygon count of every job in cc5_jobs\batch.txt (loads each .ccProject).
# -> cc5_jobs\poly_report.json  {job: {"Clothes": {name: [verts, faces]}, "Hairs": {...}, "Body": {...}}}
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

out = {}
for d in open(kit.BATCH, encoding="utf-8").read().splitlines():
    d = d.strip()
    if not d:
        continue
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
    proj = os.path.join(d, name + ".ccProject")
    if not os.path.exists(proj):
        continue
    RLPy.RFileIO.LoadFile(proj)
    av = RLPy.RScene.GetAvatars()[0]
    rep = {}
    for kind, objs in (("Clothes", av.GetClothes()), ("Hairs", av.GetHairs()), ("Accessories", av.GetAccessories()), ("Body", [av])):
        part = {}
        for o in objs:
            for m in o.GetMeshes():
                part[o.GetName() + "/" + m.GetName()] = [m.GetVerticesCount(), m.GetFacesCount()]
        rep[kind] = part
    out[os.path.basename(d)] = rep
    json.dump(out, open(os.path.join(kit.JOBS, "poly_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(kit.JOBS, "poly_report.json"), "a").write("\n")
