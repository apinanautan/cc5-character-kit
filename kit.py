# Shared paths/helpers for the CC5 character kit. Works in system Python AND inside CC5 (stdlib only).
# Paths come from config.json (written by install.bat); anything missing falls back to the defaults below.
import json, os

REPO = os.path.dirname(os.path.abspath(__file__))
_L = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
DEFAULTS = {
    "program": os.path.join(_L, "Tidmunz Studio"),                    # Tidmunz Studio install (faces, hair picker)
    "blender": r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
    "library": r"G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม",
    "out_root": os.path.join(os.path.expanduser("~"), "Desktop"),        # story folders go here
}
try:
    CFG = dict(DEFAULTS, **json.load(open(os.path.join(REPO, "config.json"), encoding="utf-8")))
except (OSError, ValueError):
    CFG = dict(DEFAULTS)

PROGRAM = CFG["program"]
DATA = os.path.join(PROGRAM, "snapgen_data")          # live data (wardrobe, hair pool) — copies kept in REPO\data
JOBS = os.path.join(DATA, "cc5_jobs")                  # one folder per character job
BATCH = os.path.join(JOBS, "batch.txt")                # job folders for cc5\build.py (first line = "current" job)
BLENDER = CFG["blender"]
LIB = CFG["library"]
FABRICS = os.path.join(REPO, "data", "fabrics")
# short prefixes usable in story outfits
PREFIX = {"MO:": os.path.join(LIB, "!Converted STUFFS", "Male Outfits"),
          "RC:": os.path.join(LIB, "Reallusion Custom", "Cloth"),
          "LIB:": LIB}


def data_file(name):
    """Live copy in snapgen_data if it exists, else the repo snapshot."""
    live = os.path.join(DATA, name)
    return live if os.path.exists(live) else os.path.join(REPO, "data", name)


def current_job():
    return open(BATCH, encoding="utf-8").read().split("\n")[0].strip()


def set_batch(dirs):
    os.makedirs(JOBS, exist_ok=True)
    open(BATCH, "w", encoding="utf-8").write("\n".join(os.path.normpath(d) for d in dirs))


def resolve_item(spec, wardrobe=None):
    """'f7c187' (wardrobe id prefix) | 'MO:Owen\\Pants.ccCloth' | full path  ->  full path."""
    for p, root in PREFIX.items():
        if spec.startswith(p):
            return os.path.join(root, spec[len(p):])
    if os.path.isabs(spec):
        return spec
    if wardrobe is None:
        wardrobe = {i["id"]: i["path"] for i in json.load(open(data_file("wardrobe_verified.json"), encoding="utf-8"))["items"]}
    hit = [p for k, p in wardrobe.items() if k.startswith(spec)]
    if len(hit) != 1:
        raise KeyError("wardrobe id %r matches %d items" % (spec, len(hit)))
    return hit[0]


def load_story(name):
    path = name if name.endswith(".json") else os.path.join(REPO, "stories", name + ".json")
    s = json.load(open(path, encoding="utf-8-sig"))
    s["out_dir"] = os.path.expandvars(s.get("out_dir", os.path.join(CFG["out_root"], s["title"])))
    return s
