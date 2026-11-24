# Register / update jobs shown in the progress window (tools\progress_widget.py reads tools\progress_jobs.json every 3 s).
#   python tools\progress.py add  "<name>" --total N --files "glob" ["glob2" ...]      progress = number of files matching
#   python tools\progress.py add  "<name>" --total N --json-glob "runs/.../part_*.json"  progress = rows in those json files
#   python tools\progress.py add  "<name>" --total N                                    manual: then use  set
#   python tools\progress.py set  "<name>" <value>        (manual jobs: how many are done)
#   python tools\progress.py remove "<name>" | clear-done | list
# Paths are relative to the project folder. A finished job shows "done" for a minute, then the window hides it.
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "tools", "progress_jobs.json")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load():
    try:
        return json.load(open(CFG, encoding="utf-8"))
    except Exception:
        return []


def save(jobs):
    json.dump(jobs, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


ap = argparse.ArgumentParser()
ap.add_argument("cmd"); ap.add_argument("name", nargs="?"); ap.add_argument("value", nargs="?", type=int)
ap.add_argument("--total", type=int); ap.add_argument("--files", nargs="*"); ap.add_argument("--json-glob")
a = ap.parse_args()
jobs = load()
if a.cmd == "add":
    jobs = [j for j in jobs if j["name"] != a.name]
    j = {"name": a.name, "total": a.total or 1}
    if a.files: j["count_files"] = a.files
    elif a.json_glob: j["count_json_glob"] = a.json_glob
    else: j["value"] = 0
    jobs.append(j)
elif a.cmd == "set":
    for j in jobs:
        if j["name"] == a.name: j["value"] = a.value
elif a.cmd == "remove":
    jobs = [j for j in jobs if j["name"] != a.name]
elif a.cmd == "list":
    for j in jobs: print(j)
    sys.exit()
save(jobs)
print("jobs:", [j["name"] for j in jobs])
