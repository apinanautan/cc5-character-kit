
# QA-only: export the successful child's actual skinned clothes as reusable CC clothing.
# Run: python tools/cc5.py run cc5/probes/qa_export_kid_cloth.py job=<05 folder> out=<06 qa folder>
import os, json
import RLPy
A = BRIDGE_ARGS
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
outdir = A["out"]
os.makedirs(outdir, exist_ok=True)
log = []
for c in av.GetClothes():
    n = c.GetName()
    role = "shirt" if n == "node_0" else ("jong" if n == "new" else "other")
    if role == "other":
        log.append("SKIP " + n)
        continue
    setting = RLPy.RSaveFileSetting()
    setting.SetSaveType(RLPy.ESaveFileType_Upper if role == "shirt" else RLPy.ESaveFileType_Lower)
    dest = os.path.join(outdir, "donor_" + role + ".ccCloth")
    try:
        result = RLPy.RFileIO.SaveFile(av, setting, dest)
        log.append("%s %s is_error=%s bytes=%d" % (role, n, result.IsError(), os.path.getsize(dest) if os.path.isfile(dest) else 0))
    except Exception as e:
        log.append("%s exception=%s" % (role, e))
BRIDGE_RESULT = "\n".join(log)
