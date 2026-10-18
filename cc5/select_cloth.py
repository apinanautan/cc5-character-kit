# CC5 > Script > Load Python: load the current job's project (first line of batch.txt) and select one garment
# by name (cc5_jobs\select_cloth.txt), e.g. before Modify > InstaLOD > Polygon Reduction - Object.
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

d = kit.current_job()
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
want = open(os.path.join(kit.JOBS, "select_cloth.txt"), encoding="utf-8").read().strip()
proj = os.path.join(d, name + ".ccProject")
RLPy.RFileIO.LoadFile(proj)  # always start from the saved project
av = RLPy.RScene.GetAvatars()[0]
for cl in av.GetClothes():
    if cl.GetName() == want:
        RLPy.RScene.SelectObject(cl)
        break
