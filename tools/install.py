# One-time setup on a (new) PC: python tools\install.py   (install.bat runs this)
# - finds Blender, Tidmunz Studio, the clothes library -> writes config.json (edit it by hand if a path is wrong)
# - restores wardrobe / hair data into snapgen_data if they are missing (repo copies in data\)
# - installs the Python packages the tools need (Pillow, numpy)
import glob, json, os, shutil, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.environ.get("LOCALAPPDATA", "")
ok = True


def say(tag, msg):
    print("%-6s %s" % (tag, msg))


subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pillow", "numpy"])

blenders = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"))
pref = [b for b in blenders if "4.2" in b]  # tested with 4.2
blender = (pref or blenders or [""])[-1]
program = os.path.join(L, "Tidmunz Studio")
lib_candidates = [r"G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม",
                  r"G:\My Drive\เสื้อผ้า-ทรงผม", r"D:\เสื้อผ้า-ทรงผม"]
library = next((p for p in lib_candidates if os.path.isdir(p)), lib_candidates[0])
cfg_path = os.path.join(REPO, "config.json")
cfg = json.load(open(cfg_path, encoding="utf-8")) if os.path.exists(cfg_path) else {}
cfg.setdefault("blender", blender)
cfg.setdefault("program", program)
cfg.setdefault("library", library)
cfg.setdefault("out_root", os.path.join(os.path.expanduser("~"), "Desktop"))
json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
say("OK", "config.json written")

for key, what in (("blender", "Blender (shirt in/out fix)"), ("program", "Tidmunz Studio (faces, hair picker)"),
                  ("library", "clothes/hair library")):
    if os.path.exists(cfg[key]):
        say("OK", "%s: %s" % (what, cfg[key]))
    else:
        ok = False
        say("MISSING", "%s: %s  -> install it or fix the path in config.json" % (what, cfg[key]))

cc5 = r"C:\Program Files\Reallusion\Character Creator 5\Bin64\CharacterCreator.exe"
say("OK" if os.path.exists(cc5) else "MISSING", "Character Creator 5: " + cc5)

data = os.path.join(cfg["program"], "snapgen_data")
if os.path.isdir(cfg["program"]):
    os.makedirs(os.path.join(data, "cc5_jobs"), exist_ok=True)
    for name in ("wardrobe_verified.json", "cc5_hair_pool.json", "cc5_wardrobe.json"):
        live = os.path.join(data, name)
        if not os.path.exists(live):
            shutil.copy(os.path.join(REPO, "data", name), live)
            say("OK", "restored " + name + " from the repo")
print()
print("Ready." if ok else "Fix the MISSING lines above, then run install.bat again.")
print("Next: python tools\\gen_faces.py <story>  ->  python tools\\plan.py <story>  ->  CC5: Script > Load Python > cc5\\build.py")
