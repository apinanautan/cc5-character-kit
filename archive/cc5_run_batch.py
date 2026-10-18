# Run inside CC5 (Script > Load Python) ONCE: builds every job listed in cc5_jobs\batch_luek.txt in a row.
# Skips jobs that already have <name>.ccProject. Each job writes its own result.txt.
import json, os
JOBS = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
SCRIPT = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_modules", "cc5", "cc5_build_character.py")
for d in open(os.path.join(JOBS, "batch_luek.txt"), encoding="utf-8").read().split("\n"):
    d = d.strip()
    if not d:
        continue
    name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8"))["name"]
    if os.path.exists(os.path.join(d, name + ".ccProject")):
        continue
    open(os.path.join(JOBS, "current_job.txt"), "w", encoding="utf-8").write(d)
    try:
        exec(compile(open(SCRIPT, encoding="utf-8").read(), SCRIPT, "exec"), {"__file__": SCRIPT, "__name__": "__main__"})
    except Exception as e:
        open(os.path.join(d, "result.txt"), "a", encoding="utf-8").write("\nBATCH FAIL %r" % e)
