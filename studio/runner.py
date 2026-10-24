# Story -> finished .iAvatar files, one character at a time, step by step (used by app.py).
# Each step's status is saved in the story file ("status"), so a stopped run continues where it left off.
import json, os, random, re, subprocess, sys, time, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
import planner, wardrobe, fabric_ai

PY = sys.executable.replace("pythonw.exe", "python.exe")
NOWIN = 0x08000000
STEPS = [("plan", "แผน"), ("fabric", "ลายผ้า"), ("face", "หน้า"), ("build", "สร้างตัว"), ("scar", "แผล"),
         ("weights", "แขน"), ("export", "iAvatar")]
SKIN = ["ผิวสองสี", "ผิวคล้ำแดด", "ผิวขาวเหลือง", "ผิวสีน้ำผึ้ง", "ผิวคล้ำ"]
FACE = ["หน้ากลม", "หน้ารูปไข่", "หน้าเหลี่ยม", "หน้ายาว", "แก้มป่อง", "โหนกแก้มสูง"]
FEATURE = ["ตาชั้นเดียว", "ตาสองชั้น", "จมูกแบนเล็ก", "จมูกโด่งเล็กน้อย", "ปากหนา", "ปากบาง", "คิ้วหนา", "คิ้วบาง",
           "ตาเล็กเรียว", "ตากลมโต", "คางสั้น", "คางแหลม"]
MORPH_THIN = {"2019-09-30-13-56-29_face thinner": 0.8}  # the full-body skinny pack asks for a licence -> not used
MORPH_PREGNANT = {"cc embed morphs/embed_torso113": 1.0, "cc embed morphs/embed_torso111": 1.0}


def slug_of(title):
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return (s or "story") + time.strftime("_%m%d_%H%M")


def create_story(title, rows, out_root=None):
    """rows from planner.parse (edited in the app) -> stories/<slug>.json with outfit/hair/face for everyone."""
    slug = slug_of(title)
    used, before = wardrobe.new_story_used(), wardrobe.used_before(slug)
    chars, jobs_by_person = {}, {}
    for i, r in enumerate([r for r in rows if r.get("use", True)]):
        job = "%s_%02d" % (slug, i + 1)
        sex, age = r["sex"] if r["sex"] in ("m", "f") else "m", int(r["age"])
        group = planner.age_group(age)
        outfit, layer, designs = wardrobe.pick_outfit(sex, group, used, before, r.get("notes", ""),
                                                      r.get("outfit", ""), age)
        hair, rgb = wardrobe.pick_hair(sex, group, used, before)
        person = r.get("person") or planner.base_name(r["name"])
        c = {"name": r["name"], "sex": "male" if sex == "m" else "female", "age": age, "age_group": group,
             "body": "baby" if group == "baby" else "child" if group == "child" else "neutral",
             "folder": r.get("folder", ""), "notes": r.get("notes", ""), "outfit": outfit, "layer": layer,
             "style": r.get("outfit", ""),
             "fabric_designs": designs}
        if hair:
            c["hair"] = hair
            c["hair_rgb"] = rgb
        hair_txt = {"child": "ผมดำ", "adult": "ผมดำ", "middle": "ผมดอกเลาสีเทา", "old": "ผมขาว"}.get(group, "")
        c["face"] = {"อายุ": "ทารกอายุประมาณ 1 ขวบ" if group == "baby" else "ประมาณ %d ปี" % age,
                     "เพศ": "ชาย" if sex == "m" else "หญิง",
                     "บทบาท": r["name"] + (" (" + r["role"] + ")" if r.get("role") else ""),
                     "สีผิว": random.choice(SKIN if group != "old" else SKIN[:2] + SKIN[4:]),
                     "ทรงผม": hair_txt, "ใบหน้า": " ".join([random.choice(FACE)] + random.sample(FEATURE, 2)),
                     "prompt_name": r["name"]}
        notes = r.get("notes", "")
        same = jobs_by_person.get(person, [])
        prev = min(same, key=lambda j: abs(chars[j]["age"] - age)) if same else None
        if prev:  # same person again: look alike; about the same age (burn / thin / pregnant) = the very same head
            pc = chars[prev]
            c["face"]["ref"] = prev
            c["face"]["สีผิว"] = pc["face"].get("สีผิว", "") if "face" in pc else c["face"]["สีผิว"]
            c["face"]["ใบหน้า"] = pc["face"].get("ใบหน้า", "") if "face" in pc else c["face"]["ใบหน้า"]
            if abs(pc["age"] - age) <= 6 and group == pc["age_group"]:
                c["head_from"] = pc.get("head_from", prev)
                c.pop("face")
                if "hair" in pc:
                    c["hair"], c["hair_rgb"] = pc["hair"], pc.get("hair_rgb")
        if "ผอม" in notes:
            c["morphs"] = dict(MORPH_THIN)
        if "ท้อง" in notes:
            c["morphs"] = dict(MORPH_PREGNANT)
        jobs_by_person.setdefault(person, []).append(job)
        chars[job] = c
    story = {"title": title, "era": "คนไทยต่างจังหวัด ยุคปัจจุบัน", "slug": slug,
             "out_dir": os.path.join(out_root or kit.CFG["out_root"], title), "characters": chars,
             "status": {j: {"plan": "ok"} for j in chars}}
    path = os.path.join(kit.REPO, "stories", slug + ".json")
    save(path, story)
    wardrobe.remember(slug, chars)
    return path


def save(path, story):
    tmp = path + ".tmp"
    json.dump(story, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load(path):
    return json.load(open(path, encoding="utf-8-sig"))


def _run(args, timeout=3600):
    r = subprocess.run([PY] + args, cwd=kit.REPO, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=NOWIN)
    return r.returncode, (r.stdout + r.stderr).strip()


def cc5_run(script, timeout=3600, **args):
    return _run([os.path.join("tools", "cc5.py"), "run", script] + ["%s=%s" % kv for kv in args.items()], timeout)


def cc5_up(restart=False):
    hb = os.path.join(kit.JOBS, "bridge", "heartbeat.txt")
    try:
        stale = time.time() - os.path.getmtime(hb) > 60
    except OSError:
        stale = True
    # CC5 open but not answering (hung after a crash/heavy load) -> restart it instead of queueing work behind it
    return _run([os.path.join("tools", "start_cc5.py")] + (["--restart"] if restart or stale else []), 900)


def tidmunz_running():
    # Tidmunz Studio = pythonw.exe running snapgen_gui_v2.py (its window title is Thai, so look at command lines)
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                          "Where-Object { $_.CommandLine -match 'snapgen_gui' }).Count"],
                         capture_output=True, text=True, creationflags=NOWIN).stdout.strip()
    return out.isdigit() and int(out) > 0


_tidmunz_started = [0.0]


def tidmunz_up(log):
    if tidmunz_running():
        return
    if time.time() - _tidmunz_started[0] < 600:  # launched a moment ago, still starting: never open a second one
        time.sleep(20)
        return
    exe = os.path.join(os.path.expanduser("~"), "Desktop", "Tidmunz Studio.exe")
    if os.path.exists(exe):
        log("เปิด Tidmunz Studio (ใช้สร้างหน้า/ลายผ้า) ...")
        _tidmunz_started[0] = time.time()
        subprocess.Popen([exe])
        for _ in range(30):
            time.sleep(5)
            if tidmunz_running():
                time.sleep(30)  # let its ChatGPT bridge come up
                return


class Runner:
    def __init__(self, story_path, opts, on_update):
        self.path, self.opts, self.on_update = story_path, opts, on_update
        self.stop = False
        self.exported_since_restart = 0

    # ---- helpers ----
    def log(self, msg):
        self.on_update("log", msg)

    def set(self, job, step, value):
        s = load(self.path)
        s.setdefault("status", {}).setdefault(job, {})[step] = value
        save(self.path, s)
        self.on_update("status", (job, step, value))

    def job_dir(self, job):
        return os.path.join(kit.JOBS, job)

    def png(self, job, c):
        return os.path.join(self.job_dir(job), c["name"] + ".png")

    # ---- steps ----
    def step_fabric(self, job, c, story):
        changed, notes = False, []
        for item in c["outfit"]:
            fab = item[1]
            if not fab or not fab.startswith("gen:"):
                continue
            design = fab[4:]
            path = None
            if self.opts.get("ai_fabric", True):
                try:
                    tidmunz_up(self.log)
                    path = fabric_ai.make(design)
                    item[1] = fabric_ai.name_of(design)
                    notes.append(design)
                except Exception as e:
                    self.log("สร้างลายผ้า AI ไม่ได้ (%s) ใช้ผ้าในคลังแทน" % str(e)[:80])
            if not path:
                lib = [os.path.splitext(f)[0] for f in os.listdir(kit.FABRICS) if f.endswith(".png") and "plaid" not in f]
                item[1] = random.choice(lib)
                notes.append("คลัง:" + item[1])
            changed = True
        if changed:
            s = load(self.path)
            s["characters"][job]["outfit"] = c["outfit"]
            save(self.path, s)
        return "ok", ", ".join(notes) or "ไม่ต้องใช้"

    def step_face(self, job, c, story):
        if c.get("head_from"):
            return "skip", "ใช้หัวเดียวกับ " + story["characters"][c["head_from"]]["name"]
        face = os.path.join(self.job_dir(job), "face.png")
        if os.path.exists(face):
            return "ok", "มีหน้าแล้ว"
        ref = c.get("face", {}).get("ref")
        if ref and not os.path.exists(os.path.join(self.job_dir(ref), "face.png")):
            return "fail", "ต้องทำหน้าของ %s ก่อน" % story["characters"][ref]["name"]
        tidmunz_up(self.log)
        code, out = _run([os.path.join("tools", "gen_faces.py"), self.path, job], 900)
        if os.path.exists(face):
            self.on_update("image", face)
            return "ok", ""
        return "fail", (out.splitlines() or ["?"])[-1][:200]

    def step_build(self, job, c, story):
        src = c.get("head_from")
        if src:
            sname = story["characters"][src]["name"]
            if not os.path.exists(os.path.join(self.job_dir(src), sname + ".ccProject")):
                return "fail", "ต้องสร้าง %s ให้เสร็จก่อน" % sname
        code, out = _run([os.path.join("tools", "plan.py"), self.path, job], 600)
        if code:
            return "fail", "เตรียมงานไม่ได้: " + out[-200:]
        cc5_up()
        for attempt in range(2):
            code, out = cc5_run(os.path.join("cc5", "build.py"))
            res = os.path.join(self.job_dir(job), "result.txt")
            text = open(res, encoding="utf-8", errors="replace").read() if os.path.exists(res) else out
            fails = [l for l in text.splitlines() if l.startswith("FAIL") or "BATCH FAIL" in l]
            m = re.search(r"clothes_count: (\d+)", text)
            if m and not fails and int(m.group(1)) < len(c["outfit"]):
                return "fail", "ชุดหลุด: ใส่ได้ %s จาก %d ชิ้น (คู่เสื้อกับกางเกงชนกัน) กด สุ่มชุดใหม่" % (m.group(1), len(c["outfit"]))
            if not os.path.exists(res):
                fails = ["build.py ไม่ได้ทำงาน (ไม่มี result.txt): " + out[-150:]]
            if not fails and os.path.exists(self.png(job, c)):
                self.on_update("image", self.png(job, c))
                return "ok", ""
            self.log("สร้างตัวไม่ผ่าน: %s -> เปิด CC5 ใหม่แล้วลองอีกครั้ง" % (fails[:1] or [out[-120:]]))
            if os.path.exists(res):
                os.remove(res)
            cc5_up(restart=True)
            _run([os.path.join("tools", "plan.py"), self.path, job], 600)
        return "fail", (fails[:1] or [out[-200:]])[0][:200]

    def _open(self, job):
        for attempt in range(3):
            code, out = cc5_run(os.path.join("cc5", "open_job.py"), 600, job=job)
            if "avatars=1" in out:
                return True
            if attempt == 1:
                cc5_up(restart=True)
        return False

    def step_scar(self, job, c, story):
        m = re.search(r"แผลไฟไหม้ที่(\S+)", c.get("notes", ""))
        if not m:
            return "skip", ""
        where = {"แขน": "arm", "หน้า": "face", "ขา": "leg"}.get(m.group(1), "arm")
        spot = {"arm": [600, 1130, 230, 300], "face": [560, 1150, 150, 120], "leg": [560, 1300, 200, 260]}[where]
        tex = os.path.join(self.job_dir(job), "scar_%s.png" % where)
        code, out = _run([os.path.join("tools", "scar_overlay.py"), tex] + [str(v) for v in spot] + [str(random.randint(1, 999))])
        if not os.path.exists(tex):
            return "fail", "วาดแผลไม่ได้: " + out[-150:]
        code, out = cc5_run(os.path.join("cc5", "scar.py"), 900, job=job, where=where, tex=tex)
        if "OK scar" in out:
            self.on_update("image", self.png(job, c))
            return "ok", where
        return "fail", (out.splitlines() or ["?"])[-1][:200]

    def step_weights(self, job, c, story):
        if not self.opts.get("weights") or c.get("age_group") == "baby":
            return "skip", ""
        code, out = cc5_run(os.path.join("cc5", "fix_weights.py"), 900, job=job, save="1")
        if "saved" in out:
            self.on_update("image", os.path.join(self.job_dir(job), "weights_after.png"))
            return "ok", ""
        return "fail", (out.splitlines() or ["?"])[-1][:200]

    def step_export(self, job, c, story):
        if not self.opts.get("export", True):
            return "skip", "export เอง"
        import export_ui
        target = os.path.join(story["out_dir"], c.get("folder", ""), c["name"] + ".iAvatar")
        if not self._open(job):
            return "fail", "เปิดตัวละครใน CC5 ไม่ได้"
        ok, msg = export_ui.export(target, self.job_dir(job))
        if ok:
            self.exported_since_restart += 1
            return "ok", msg
        return "fail", msg

    # ---- main loop ----
    def run(self):
        story = load(self.path)
        jobs = [j for j in story["characters"] if not self.opts.get("only") or j in self.opts["only"]]
        for job in jobs:
            for key, label in STEPS:
                if self.stop:
                    self.log("หยุดแล้ว")
                    self.on_update("done", None)
                    return
                story = load(self.path)
                c = story["characters"][job]
                st = story.get("status", {}).get(job, {}).get(key, "")
                if st in ("ok", "skip") or st.startswith("ok") or st.startswith("skip"):
                    continue
                if any(v.startswith("fail") for v in story.get("status", {}).get(job, {}).values()):
                    break  # this character failed earlier: go on with the next one
                if key == "plan":
                    self.set(job, key, "ok")
                    continue
                self.set(job, key, "run")
                self.log("%s: %s ..." % (c["name"], label))
                try:
                    res, msg = getattr(self, "step_" + key)(job, c, story)
                except Exception:
                    res, msg = "fail", traceback.format_exc().splitlines()[-1][:200]
                self.set(job, key, res + (": " + msg if msg else ""))
                self.log("%s: %s -> %s %s" % (c["name"], label, res, msg))
                if res == "fail":
                    break
            if self.exported_since_restart >= 1:  # fresh CC5 for every character: its RAM grows to 15-18 GB otherwise
                self.log("พัก: เปิด CC5 ใหม่")
                cc5_up(restart=True)
                self.exported_since_restart = 0
        st = load(self.path).get("status", {})
        bad = [story["characters"][j]["name"] for j in jobs if any(str(v).startswith("fail") for v in st.get(j, {}).values())]
        self.log("จบรอบ: " + ("มีตัวที่พัง %d ตัว: %s (เลือกแล้วกด ทำใหม่)" % (len(bad), ", ".join(bad)) if bad else "เสร็จครบทุกตัว"))
        self.on_update("done", None)


def reset(path, job, from_step="fabric", keep_face=False):
    """Redo a character from a step (app button 'ทำใหม่')."""
    s = load(path)
    keys = [k for k, _ in STEPS]
    st = s.setdefault("status", {}).setdefault(job, {})
    for k in keys[keys.index(from_step):]:
        st.pop(k, None)
    d = os.path.join(kit.JOBS, job)
    for f in ("result.txt", "upper.txt", "layer_fix.txt") + (("face.png",) if from_step in ("fabric", "face") and not keep_face else ()):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    save(path, s)


def reroll(path, job):
    """New random outfit/fabric for one character (keeps face)."""
    s = load(path)
    c = s["characters"][job]
    used = wardrobe.new_story_used()
    for j, o in s["characters"].items():
        if j != job:
            used["tops"].append(o["outfit"][1][0] if len(o["outfit"]) > 1 else "")
            used["bottoms"].append(o["outfit"][0][0])
            used["fabrics"] += o.get("fabric_designs", [])
    outfit, layer, designs = wardrobe.pick_outfit("m" if c["sex"] == "male" else "f", c["age_group"], used,
                                                  wardrobe.used_before(s.get("slug", "")), c.get("notes", ""),
                                                  c.get("style", ""), c.get("age", 30))
    c.update(outfit=outfit, layer=layer, fabric_designs=designs)
    save(path, s)
    reset(path, job, "fabric", keep_face=True)
    s = load(path)
    s["status"][job]["face"] = "ok" if os.path.exists(os.path.join(kit.JOBS, job, "face.png")) else ""
    save(path, s)
