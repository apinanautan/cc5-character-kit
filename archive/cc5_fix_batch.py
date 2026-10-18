# Run inside CC5: reopen each job's .ccProject from cc5_jobs\batch_fix.txt and re-dress it (skip_headshot jobs).
import json, os
import RLPy
JOBS = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
SCRIPT = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_modules", "cc5", "cc5_build_character.py")
for d in open(os.path.join(JOBS, "batch_fix.txt"), encoding="utf-8").read().split("\n"):
    d = d.strip()
    if not d:
        continue
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
    RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
    open(os.path.join(JOBS, "current_job.txt"), "w", encoding="utf-8").write(d)
    exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), {"__file__": SCRIPT, "__name__": "__main__"})
