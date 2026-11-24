# Re-hair the characters of a story in one go and export each to Drive (sheet folder from runs/<story>_renders/list.json).
#   python tools\rehair_story.py          (mapping below: Drive file name -> (hair index in cand_custom_hair.json | "none", rgb))
# Log: runs/rehair_log.txt . Skips characters already done (listed in runs/rehair_done.json), so it can be started again after a stop.
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
STORY = "ดวงเมียน้อย"
BLACK, GRAY = "18,16,15", "120,118,115"
MAP = {  # new hair per character (black unless noted); nari (folder 2) is already done
    "ปรีชา": (89, BLACK), "สุนีย์": (60, BLACK), "นิวัตน์วัยป2": (55, BLACK), "นิวัตน์วัยป5": (66, BLACK), "เมียน้อยปรีชา": (71, BLACK),
    "ชาวบ้านชาย1": (53, BLACK), "ชาวบ้านหญิง1": (70, BLACK), "วินัยวัยมัธยม": (86, BLACK), "วินัยตำรวจฝึกหัด": (75, BLACK), "วินัยตำรวจ": (58, BLACK),
    "เถ้าแก่โรงงานขนม": (98, GRAY), "พีภพ": (67, BLACK), "ปรียา": (91, BLACK), "ปรียาตั้งครรภ์": (91, BLACK),
    "อรทัย": (90, BLACK), "อรทัยชุดนักศึกษา": (90, BLACK), "รุ่นพี่มหาลัยชาย1": (83, BLACK), "รุ่นพี่มหาลัยหญิง1": (76, BLACK),
    "หญิงปฏิบัติธรรม1": ("none", BLACK), "หญิงปฏิบัติธรรม2": ("none", BLACK),
}
lst = json.load(open(os.path.join(ROOT, "runs", STORY + "_renders", "list.json"), encoding="utf-8"))
hairs = json.load(open(os.path.join(ROOT, "runs", "wardrobe_scan", "cand_custom_hair.json"), encoding="utf-8"))
donef = os.path.join(ROOT, "runs", "rehair_done.json")
done = json.load(open(donef, encoding="utf-8")) if os.path.exists(donef) else []
log = open(os.path.join(ROOT, "runs", "rehair_log.txt"), "a", encoding="utf-8")
say = lambda m: (log.write(time.strftime("%H:%M:%S ") + m + "\n"), log.flush(), print(m, flush=True))
byname = {}
for d in os.listdir(JOBS):
    jf = os.path.join(JOBS, d, "job.json")
    if os.path.exists(jf):
        try:
            byname.setdefault(json.load(open(jf, encoding="utf-8-sig"))["name"], []).append(d)
        except Exception:
            pass


def cc5(*a, t=400):
    r = subprocess.run([sys.executable, "tools/cc5.py", "run", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=t)
    return (r.stdout.strip().splitlines() or ["?"])[-1]


for e in lst:
    n = e["name"]
    if n not in MAP or n in done:
        continue
    idx, rgb = MAP[n]
    jobs = [j for j in byname.get(n, []) if os.path.exists(os.path.join(JOBS, j, n + ".ccProject"))]
    if not jobs:
        say("SKIP %s: no job project found" % n); continue
    job = sorted(jobs)[-1]; proj = os.path.join(JOBS, job, n + ".ccProject")
    bak = os.path.join(JOBS, job, "before_newhair_" + n + ".ccProject")
    if not os.path.exists(bak):
        import shutil; shutil.copy2(proj, bak)
    hair = "none" if idx == "none" else hairs[idx]["path"]
    try:
        a = cc5("cc5/probes/open_path.py", "path=" + proj)
        b = cc5("cc5/swap_hair.py", "hair=" + hair, "out=" + os.path.join(JOBS, job, "hair"), "rgb=" + rgb, "save=" + proj)
        c = subprocess.run([sys.executable, "tools/export_open.py", STORY, e["folder"], n, job, "drive"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=400).stdout.strip().splitlines()
        ok = bool(c) and "True" in c[-1]
        say("%s %s -> %s | %s | %s" % ("OK" if ok else "EXPORT?", n, idx, b[:60], c[-1] if c else "no output"))
        if ok:
            done.append(n); json.dump(done, open(donef, "w", encoding="utf-8"), ensure_ascii=False)
            subprocess.run([sys.executable, "tools/progress.py", "set", "เปลี่ยนผมตัวละครดวงเมียน้อย + ส่งออกไดรฟ์", str(len(done))], cwd=ROOT, capture_output=True)
    except Exception as ex:
        say("FAIL %s: %s" % (n, str(ex)[:100]))
say("finished: %d done" % len(done))
