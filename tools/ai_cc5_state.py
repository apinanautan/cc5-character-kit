"""File state shared by the Ai-cc5 command and its progress window."""

import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = (
    ("preflight", "ตรวจความพร้อม", "AI", "รัน preflight --runtime และหยุดทันทีเมื่อ BLOCKED"),
    ("select", "เลือกตัว", "AI + ผู้ใช้", "เลือกหนึ่ง actor key ที่ระบุช่วงวัยตามลำดับที่ผู้ใช้กำหนด"),
    ("open", "เปิดงาน", "AI + ผู้ใช้อนุญาต", "เปิดโปรเจกต์ต้นฉบับใน CC5 ที่เปิดอยู่ รอ texture ≥15 วิและตรวจภาพหน้าต่อเนื่อง"),
    ("fit", "ใส่ชุด", "AI + ผู้ใช้อนุญาต", "ใช้ --fit หรือ donor map หนึ่ง actor และบันทึก .ccProject แยกตาม label"),
    ("render", "เรนเดอร์", "AI + ผู้ใช้อนุญาต", "เรนเดอร์หน้า ข้าง หลัง T-Pose และคลิปเดินที่เฟรม 0/24/44"),
    ("sheet", "ภาพรวม", "AI", "ใช้ make_actor_review.py สร้าง review.png จากภาพรอบนี้"),
    ("send", "ส่งภาพ", "AI", "ส่ง PNG ไป Pic-Gptz เก็บใบยืนยันและ dedup ด้วย SHA-256"),
    ("approve", "รอผู้ใช้", "ผู้ใช้", "หลังส่งภาพตรวจสำเร็จ ให้กดอนุมัติใน Preview หรืออนุมัติในแชต"),
    ("export", "ส่งออก", "AI + ผู้ใช้อนุญาต", "ใช้ --export-reviewed และเปิด .iAvatar กลับใน CC5 พร้อมหลักฐาน"),
    ("qa", "QA", "AI", "ดูหลักฐานจริง ตรวจ Q01–Q10 และบันทึกผลรายข้อใน qa.json"),
    ("tidy", "เก็บงาน", "AI", "ใช้ tidy กับ staging ของงานที่ผ่าน QA และมี build สำเร็จ"),
)
PREPARATION = (
    ("รับบรีฟ", "01_brief.md"),
    ("วิเคราะห์เรื่อง", "02_analysis.md"),
    ("ออกแบบตัวละคร", "03_lookbook.md"),
    ("ตรวจความพร้อม", "04_preflight.json"),
    ("ไฟล์รายชื่อตัวละคร", "รายชื่อตัวละคร.rtf"),
)
FRAMES = ("front", "side", "back", "t_front", "t_side", "walk_00", "walk_40",
          "walk_40_side", "walk_74_side")
QA_KEYS = tuple(f"Q{i:02d}" for i in range(1, 11))
BANGKOK = timezone(timedelta(hours=7))


class Blocked(Exception):
    """User decision or missing prerequisite."""


def identifier(value):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}", value or ""):
        raise Blocked("ชื่อเรื่อง ตัวละคร และ label ใช้เฉพาะตัวอักษรอังกฤษ ตัวเลข _ และ -")
    return value


def load(path, default=None):
    try:
        return path_json(path)
    except FileNotFoundError:
        return default


def path_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    try:
        temp.write_bytes(content)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def save(path, data):
    atomic(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


@contextmanager
def lock(path, busy="Ai-cc5 กำลังทำงานอยู่ ให้ดู Ai-cc5 log"):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if not stream.tell():
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Blocked(busy) from exc
        yield


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def stamp():
    return datetime.now(BANGKOK).isoformat(timespec="seconds")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def png(path):
    try:
        from PIL import Image
        with Image.open(path) as image:
            if image.format != "PNG" or min(image.size) < 32:
                return False
            image.verify()
        return True
    except (OSError, ValueError, ImportError, SyntaxError):
        return False


class State:
    def __init__(self, root=ROOT):
        self.root = root
        self.runs = root / "runs"

    def active(self):
        story = load(self.runs / ".ai_cc5_active.json", {}).get("story")
        return load(self.state_file(story), {}) if story else {}

    def preparation_folder(self, story):
        return self.runs / identifier(story) / "prepare_story"

    def preparation(self, story):
        folder = self.preparation_folder(story)
        gate = load(folder / PREPARATION[3][1], {})
        rows = []
        for name, relative in PREPARATION[:3]:
            path = folder / relative
            rows.append((name, path, "พร้อม" if path.is_file() and path.stat().st_size else "รอข้อมูล"))
        gate_label = {"BLOCKED": "ต้องเตรียมเพิ่ม", "READY_FOR_NEXT_GATE": "พร้อม"}.get(gate.get("status"), "รอตรวจ")
        rows.append((PREPARATION[3][0], folder / PREPARATION[3][1], gate_label))
        state = load(self.state_file(story), {})
        report = self.cast_report(story)
        valid = False
        if report:
            try:
                expected = self.cast_report_bytes(story, state)
                valid = bool(expected and report.is_file() and report.read_bytes() == expected)
            except OSError:
                pass
        rows.append((PREPARATION[4][0], report or folder / PREPARATION[4][1], "พร้อม" if valid else "รอข้อมูล"))
        return rows, gate

    def story_manifest(self, story):
        return load(self.root / "stories" / f"{identifier(story)}.json", {})

    def story_is_draft(self, story):
        return self.story_manifest(story).get("production_stage") == "planning"

    def finished_actors(self, state):
        finished = set(state.get("finished_actors", ()))
        actor = state.get("actor")
        if actor and state.get("done") == [step[0] for step in STEPS]:
            finished.add(f'{state["story"]}_{actor}')
        return finished

    def cast_rows(self, story, state=None, manifest=None):
        manifest = self.story_manifest(story) if manifest is None else manifest
        state = load(self.state_file(story), {}) if state is None else state
        finished = self.finished_actors(state)
        actors = {k:v for k,v in (manifest.get("characters") or {}).items() if isinstance(v,dict)}
        brief = manifest.get("cast_brief") or {}
        lead = manifest.get("lead")
        important = set(manifest.get("important_characters") or ())
        used = set()
        rows = []
        def marked(k,v):
            return bool(k == lead or k in important or v.get("important") or v.get("is_main") or "ตัวเอก" in str(v.get("role","")))
        for k,v in brief.items():
            if not isinstance(v,dict): continue
            name = v.get("name") or k
            matches = [(ak,av) for ak,av in actors.items() if av.get("name")==name or ak==f"{story}_{k}" or ak.startswith(f"{story}_{k}_")]
            used.update(ak for ak,_ in matches)
            count = v.get("count",1)
            star = marked(k,v) or any(marked(ak,av) for ak,av in matches)
            if type(count) is int and count==1:
                if len(matches)>1:
                    for ak,av in matches:
                        rows.append((f"{av.get('name',name)} · {av.get('age','?')} ปี",star,ak in finished))
                else:
                    age = matches[0][1].get("age") if matches else v.get("age_for_production")
                    display = f"{name} · {age} ปี" if age is not None else name
                    rows.append((display,star,bool(matches and all(ak in finished for ak,_ in matches))))
            else:
                n = len([ak for ak,_ in matches if ak in finished])
                target = str(count) if type(count) is int else f"{count[0]}–{count[1]}" if isinstance(count,list) and len(count)==2 else "ยังไม่ระบุจำนวน"
                done = type(count) is int and count>0 and n>=count
                rows.append((f"{name} ({n}/{target})",star,done))
                for ak,av in matches:
                    rows.append((f"    {av.get('name',ak)} · {av.get('age','?')} ปี",star,ak in finished))
        for k,v in actors.items():
            if k not in used:
                name=v.get("name") or k
                age=v.get("age")
                rows.append((f"{name} · {age} ปี" if age is not None else name,marked(k,v) or marked(k.removeprefix(story+"_"),v),k in finished))
        return rows

    def cast_report(self, story):
        raw = self.story_manifest(story).get("out_dir")
        if not isinstance(raw,str) or not raw.strip(): return None
        root = Path(os.path.expandvars(raw))
        if not root.is_absolute(): return None
        return root / PREPARATION[4][1]

    def cast_report_bytes(self, story, state=None):
        rows = self.cast_rows(story,state)
        if not rows: return None
        def esc(text):
            out=[]
            for ch in str(text):
                if ch in "{}" or ch==chr(92):
                    out.append(chr(92)+ch)
                elif ord(ch)>127:
                    b=ch.encode("utf-16-le")
                    for i in range(0,len(b),2):
                        n=int.from_bytes(b[i:i+2],"little",signed=True)
                        out.append(chr(92)+"u"+str(n)+"?")
                else: out.append(ch)
            return "".join(out)
        slash=chr(92)
        head=r"{\rtf1\ansi\deff0\uc1{\fonttbl{\f0 Tahoma;}}{\colortbl;\red0\green0\blue0;\red180\green0\blue0;}\f0\fs24 "
        lines=[head+r"\cf1\b "+esc(self.story_manifest(story).get("title") or story)+r"\b0\par ",r"\fs20 "+esc("* ตัวละครสำคัญ | ดำ = ทำแล้ว | แดง = ยังไม่เสร็จ")+r"\par\par "]
        for name,star,done in rows:
            lines.append(slash+"cf"+("1" if done else "2")+" "+esc(("* " if star else "  ")+name)+r"\par ")
        return ("".join(lines)+"}").encode("ascii")

    def sync_cast_report(self, story, state=None):
        path=self.cast_report(story)
        if path is None: return None
        data=self.cast_report_bytes(story,state)
        if data is None: return None
        if not path.is_file() or path.read_bytes()!=data:
            import tempfile
            path.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(prefix=".cast_",suffix=".tmp",dir=path.parent)
            try:
                with os.fdopen(fd,"wb") as f:
                    f.write(data)
                os.replace(tmp,path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        return path

    def sent_images(self, story):
        sent=load(self.runs/identifier(story)/"flow_ntfy_receipts.json",{}).get("sent",{})
        actors=self.story_manifest(story).get("characters",{})
        records=[]
        for key,item in sent.items():
            if not isinstance(item,dict) or not item.get("id") or not item.get("hash") or item.get("topic")!="Pic-Gptz": continue
            parts=key.split("/")
            if len(parts)!=3 or not parts[0].startswith(story+"_") or parts[2]!=item["hash"]: continue
            path=Path(item.get("file") or "")
            name=actors.get(parts[0],{}).get("name") or parts[0].removeprefix(story+"_")
            kind={"face":"ใบหน้า","preview":"พรีวิว"}.get(parts[1],parts[1])
            records.append((str(item.get("at","")),name,kind,path,item["hash"],item["id"]))
        return sorted(records,key=lambda row:row[0].replace("T"," "),reverse=True)

    def actor_totals(self, state, manifest=None):
        if not state:
            return 0, 0
        if manifest is None:
            manifest = self.story_manifest(state["story"])
        characters = manifest.get("characters")
        if not isinstance(characters, dict):
            return 0, 0
        scheduled = {key for key, row in characters.items() if isinstance(row, dict)}
        return len(scheduled & self.finished_actors(state)), len(scheduled)

    def cast_target(self, manifest, scheduled):
        brief = manifest.get("cast_brief")
        entries = [row for row in brief.values() if isinstance(row, dict)] if isinstance(brief, dict) else []
        if not entries or manifest.get("cast_finalized"):
            return f"{scheduled} ตัว", scheduled, ()
        minimum, maximum = 0, 0
        pending = []
        for row in entries:
            count = row.get("count", 1)
            if type(count) is int and count > 0:
                minimum += count
                maximum += count
            elif (isinstance(count, list) and len(count) == 2
                  and all(type(value) is int for value in count) and 0 < count[0] <= count[1]):
                minimum += count[0]
                maximum += count[1]
            else:
                pending.append(row.get("name") or "ตัวละครกลุ่ม")
        label = f"{minimum} ตัว" if minimum == maximum else f"{minimum}–{maximum} ตัว"
        if pending:
            return f"{label} + {len(pending)} กลุ่ม" if maximum else f"{len(pending)} กลุ่ม", None, tuple(pending)
        return label, maximum if minimum == maximum else None, ()

    def state_file(self, story):
        return self.runs / identifier(story) / "ai_cc5_state.json"

    def write(self, state):
        save(self.state_file(state["story"]), state)
        try:
            self.sync_cast_report(state["story"],state)
        except (OSError,ValueError):
            pass

    def folder(self, state):
        return self.runs / identifier(state["story"]) / "ai_cc5" / identifier(state["label"])

    def fitting(self, state):
        if state.get("new_actor"):
            return self.folder(state)
        return (self.runs / identifier(state["story"]) / "cast_fittings" /
                identifier(state["label"]) / identifier(state["actor"]))

    def log(self, state, message):
        folder = self.folder(state)
        folder.mkdir(parents=True, exist_ok=True)
        elapsed = max(0, time.time() - state.get("started", time.time()))
        with (folder / "log.txt").open("a", encoding="utf-8") as out:
            for line in str(message).splitlines():
                if line.strip():
                    out.write(f"{stamp()} +{elapsed:.2f}s {line}\n")

    def step(self, state):
        index = len(state["done"])
        return STEPS[index] if index < len(STEPS) else None

    def evidence_progress(self, state):
        step = self.step(state)
        if not step:
            return 0, 0
        key = step[0]
        if key in ("render", "export"):
            base = self.fitting(state)
            directory = base / ("views" if key == "render" else "export_check")
            count = sum(png(directory / f"{name}.png") for name in FRAMES)
            evidence = load(directory / "runtime.json", {})
            passed = (evidence.get("reopened") is True and evidence.get("t_pose_applied") is True
                      and evidence.get("motion_applied") is True
                      and evidence.get("review_pose_discarded") is True
                      and (key != "export" or evidence.get("iavatar_reopened") is True))
            return count + int(passed), len(FRAMES) + 1
        if key == "qa":
            checks = load(self.folder(state) / "qa.json", {}).get("checks", {})
            return sum(check_record(checks.get(q)) for q in QA_KEYS), len(QA_KEYS)
        return 0, 1

    def live_detail(self, state, now=None):
        step = self.step(state)
        if not step or state.get("phase") != "กำลังทำ":
            return ""
        started = state.get("started", time.time())
        elapsed = max(0, int((time.time() if now is None else now) - started))
        detail = ""
        if state.get("new_actor") and step[0] == "fit" and state.get("build_job"):
            try:
                import kit
                path = Path(kit.JOBS) / identifier(state["build_job"]) / "progress.txt"
                if path.stat().st_mtime >= started:
                    lines = path.read_text(encoding="utf-8").splitlines()
                    last = next((line[6:] for line in reversed(lines) if line.startswith("START ")), "")
                    labels = {"headshot": "Headshot สร้างใบหน้า 3D", "strip": "เตรียมร่างกาย", "dye hair": "ปรับสีผม", "camera front": "ตั้งกล้อง", "render": "เรนเดอร์", "save": "บันทึกโปรเจกต์"}
                    detail = labels.get(last, last)
            except (OSError, ValueError, ImportError, Blocked):
                pass
        if not detail:
            detail = {"open": "สร้างใบหน้าหรือเปิดงาน", "fit": "เตรียมงาน CC5", "render": "โหลด Texture / เรนเดอร์", "export": "ส่งออก / ตรวจเปิดกลับ"}.get(step[0], step[1])
        return f"{detail} · {elapsed} วินาที"

    def progress(self, state):
        completed = len(state.get("done", ()))
        measured, total = self.evidence_progress(state) if state else (0, 0)
        return completed, round(100 * completed / len(STEPS), 1), measured, total

    def snapshot(self):
        state = self.active()
        if not state:
            return state, "ยังไม่ได้เลือกเรื่อง"
        manifest = self.story_manifest(state["story"])
        finished, scheduled = self.actor_totals(state, manifest)
        target, exact, pending = self.cast_target(manifest, scheduled)
        actor_count = f"ตัวละครเสร็จ {finished}/{exact} ตัว" if exact is not None else f"เสร็จ {finished} ตัว / ต้องทำ {target}"
        if pending:
            actor_count += f" ({', '.join(pending)} ยังไม่ระบุจำนวน)"
        if manifest.get("production_stage") == "planning" and not state.get("new_actor"):
            rows, gate = self.preparation(state["story"])
            ready = sum(status == "พร้อม" for _, _, status in rows)
            return state, f'{state["story"]} / เตรียมเรื่อง {ready}/{len(rows)} / {gate.get("status", "รอตรวจ")} / {actor_count}'
        step = self.step(state)
        completed, percent, measured, total = self.progress(state)
        status = (f'{state["story"]} / {state.get("actor") or "—"} / {state.get("age") or "—"} / '
                  f'{completed + 1 if step else completed} {step[1] if step else "เสร็จ"} / {percent:g}%')
        if step:
            status += f' | ขั้นปัจจุบัน {round(100 * measured / total)}% ({measured}/{total})'
            status += f' | {state.get("phase", "พร้อม")}'
            if state.get("phase") == "กำลังทำ":
                status += f' +{max(0, time.time() - state["started"]):.0f}s'
        return state, f"{status} | {actor_count}"

    def log_view(self, state=None):
        if state is None:
            state = self.active()
        if not state:
            return ""
        folder = self.folder(state)
        logfile = folder / "log.txt"
        tail = logfile.read_text(encoding="utf-8").splitlines()[-40:] if logfile.is_file() else []
        report = load(folder / "last_fail.json")
        if report:
            tail.extend(("", "FAIL ล่าสุด", json.dumps(report, ensure_ascii=False, indent=2)))
        return "\n".join(tail)


def check_record(record):
    return (isinstance(record, dict) and record.get("result") in ("PASS", "FIX", "REVIEW")
            and bool(str(record.get("evidence") or "").strip()))
