# Small always-on-top progress window (reads result files only, never touches the jobs).
#   pythonw tools\progress_widget.py        -- the job list (tools\progress_jobs.json) is re-read every 3 s: add/remove a job there
#                                              and it appears/disappears on its own, no restart.
# job: {"name": "...", "total": 109, "count_files": ["glob", "glob"]}   (number of files matching = progress)
#      {"name": "...", "total": 245, "count_json_glob": "runs/.../part_*.json"}   (number of rows in the json files)
#      optional "hide_when_done": true
import glob, json, os, time, tkinter as tk
from tkinter import ttk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "tools", "progress_jobs.json")
STUCK_MIN = 15


def progress(job):
    try:
        if "value" in job:   # manual job: tools\progress.py set "<name>" N
            return job["value"], None
        if job.get("count_json_glob"):
            fs = glob.glob(os.path.join(ROOT, job["count_json_glob"]))
            n = 0
            for f in fs:
                try:
                    d = json.load(open(f, encoding="utf-8")); n += len(d["items"] if isinstance(d, dict) and "items" in d else d)
                except Exception:
                    pass
            return n, max((os.path.getmtime(f) for f in fs), default=None)
        pats = job.get("count_files") or []
        pats = [pats] if isinstance(pats, str) else pats
        files = [f for p in pats for f in glob.glob(os.path.join(ROOT, p))]
        return len(files), max((os.path.getmtime(f) for f in files), default=None)
    except Exception:
        return 0, None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ความคืบหน้างาน")
        self.attributes("-topmost", True)
        self.configure(bg="#1e1f22")
        self.sig = None
        self.rows = []
        self.tick()

    def load(self):
        try:
            jobs = json.load(open(CFG, encoding="utf-8"))
            # most recently active job on top (manual jobs count as active now)
            def activity(j):
                if "value" in j:
                    return os.path.getmtime(CFG)
                return progress(j)[1] or 0
            return sorted(jobs, key=activity, reverse=True)
        except Exception:
            return []

    def rebuild(self, jobs):
        for w in self.winfo_children():
            w.destroy()
        self.rows = []
        for j in jobs:
            f = tk.Frame(self, bg="#1e1f22"); f.pack(fill="x", padx=10, pady=(8, 2))
            t = tk.Label(f, text=j["name"], fg="#e6e6e6", bg="#1e1f22", anchor="w", font=("Segoe UI", 10, "bold")); t.pack(fill="x")
            bar = ttk.Progressbar(f, length=320, maximum=max(1, j.get("total", 1))); bar.pack(fill="x", pady=2)
            s = tk.Label(f, text="", fg="#9aa0a6", bg="#1e1f22", anchor="w", font=("Segoe UI", 9)); s.pack(fill="x")
            self.rows.append((j, bar, s, f))
        if not jobs:
            tk.Label(self, text="ไม่มีงานค้าง", fg="#9aa0a6", bg="#1e1f22").pack(padx=10, pady=10)
        self.geometry("360x%d" % (14 + 66 * max(1, len(jobs))))

    def tick(self):
        jobs = self.load()
        sig = json.dumps(jobs, sort_keys=True)
        if sig != self.sig:
            self.sig = sig; self.rebuild(jobs)
        self.done_at = getattr(self, "done_at", {})
        shown = 0
        for j, bar, s, f in self.rows:
            n, mt = progress(j)
            tot = j.get("total", 0)
            bar["value"] = n
            ago = ("%d นาทีที่แล้ว" % ((time.time() - mt) // 60)) if mt else "ยังไม่มีไฟล์"
            done = bool(tot and n >= tot)
            if done:
                self.done_at.setdefault(j["name"], time.time())
            else:
                self.done_at.pop(j["name"], None)
            if done and time.time() - self.done_at[j["name"]] > 60:   # finished: show it for a minute, then hide
                f.pack_forget(); continue
            if not f.winfo_ismapped():
                f.pack(fill="x", padx=10, pady=(8, 2))
            shown += 1
            warn = " ⚠ ไม่ขยับนานแล้ว" if mt and not done and (time.time() - mt) > STUCK_MIN * 60 else ""
            s.config(text=("✓ เสร็จแล้ว  " if done else "") + "%d / %d  (%d%%)   ล่าสุด: %s%s" % (n, tot, (100 * n // tot) if tot else 0, ago, warn),
                     fg="#ffb86b" if warn else ("#5cd68a" if done else "#9aa0a6"))
        self.geometry("360x%d" % (14 + 66 * max(1, shown)))
        self.after(3000, self.tick)


if __name__ == "__main__":
    App().mainloop()
