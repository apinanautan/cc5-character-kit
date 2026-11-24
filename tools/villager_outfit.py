# Re-dress one job with plain villager pieces picked from data/base_pool.json (by index), flip-flops instead of sneakers.
#   python tools\villager_outfit.py <job> <bottom index in base_pool bottoms> <top index in base_pool tops> [shoes spec]
# Then run cc5\build.py (python tools\cc5.py run cc5\build.py) and look at the picture; export separately.
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
job, bi, ti = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
shoes = sys.argv[4] if len(sys.argv) > 4 else r"MO:Oahu\Flip Flops.ccShoes"
b = json.load(open(os.path.join(ROOT, "data", "base_pool.json"), encoding="utf-8"))
specs = [b["bottoms"][bi]["spec"], b["tops"][ti]["spec"], shoes]   # lower first, then top
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "redress.py"), job] + specs, capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip()[-300:], r.stderr.strip()[-300:])
jf = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", job, "job.json")
d = json.load(open(jf, encoding="utf-8-sig"))
d["items"] = [i for i in d["items"] if not (i.lower().endswith(".ccshoes") and not i.startswith("new"))]   # drop the old sneakers
d["layer"] = d.get("layer", "out")
json.dump(d, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("items now:", d["items"])
