# Give a finished character new clothes (keeps head, hair, shoes):
#   python tools\redress.py <job> <item[=fabric]> ...      lower garment first, then the top
#   e.g. python tools\redress.py krong_urai_40 "RC:Pants\Pants(28).ccCloth=pha_thung_green" "MO:Painter\Shirt.ccCloth=floral_brown"
# item = wardrobe id prefix (data\wardrobe_verified.json) | MO:/RC:/LIB: path in the clothes library | full path
# fabric = name of a png in data\fabrics. Then run cc5\build.py in CC5 (it loads the saved project and re-dresses it).
# Remember to copy the new outfit into the story file so a rebuild gets it too.
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
from fabric_onto_garment import make

job, specs = sys.argv[1], sys.argv[2:]
d = os.path.join(kit.JOBS, job)
jf = os.path.join(d, "job.json")
s = json.load(open(jf, encoding="utf-8-sig"))
shoes = [i for i in s["items"] if i.lower().endswith(".ccshoes")]
for f in os.listdir(d):
    if f.startswith("new") and f.lower().endswith(".cccloth"):
        os.remove(os.path.join(d, f))
items, fabrics = [], {}
for n, spec in enumerate(specs):
    it, _, fab = spec.partition("=")
    path = kit.resolve_item(it)
    dst = "new%d%s" % (n, os.path.splitext(path)[1])
    shutil.copy(path, os.path.join(d, dst))
    items.append(dst)
    if fab:
        fabrics[dst] = make(path, os.path.join(kit.FABRICS, fab + ".png"))
s["items"] = items + shoes  # hair stays from the loaded project
s["fabrics"] = fabrics
s["load_project"] = True
json.dump(s, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for f in ("result.txt", "upper.txt", "layer_fix.txt"):
    if os.path.exists(os.path.join(d, f)):
        os.remove(os.path.join(d, f))
kit.set_batch([d])
print(s["name"], s["items"], list(fabrics))
