"""One existing-actor CC5 preview step per invocation."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

from ai_cc5_state import (
    ROOT, STEPS, FRAMES, QA_KEYS, Blocked, State, atomic, check_record, digest,
    identifier, load, lock, png, save, stamp, utc_now,
)
import ai_cc5_update
from garment_pipeline import flow_preview

LIVE = {"open", "fit", "render", "export"}
NEEDED = ("review_cast.py", "qa_bridge.py", "make_actor_review.py", "CAST_QA_INVENTORY.json")


def ps(script, *args):
    return ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(script), *map(str, args)]


def capture(command, timeout=20):
    result = subprocess.run(command, capture_output=True, timeout=timeout,
                            encoding="utf-8-sig", errors="replace",
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if result.returncode:
        raise RuntimeError((result.stdout + result.stderr).strip() or f"exit {result.returncode}")
    return result.stdout.strip()


def python(script, *args):
    return [sys.executable, "-B", "-u", str(script), *map(str, args)]


def run_step_command(store, state, temp, command, timeout):
    store.log(state, subprocess.list2cmdline(command))
    stream_path = temp / "command.log"
    with stream_path.open("wb") as output, stream_path.open("rb") as reader:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                   cwd=store.root, env=os.environ | {"PYTHONIOENCODING": "utf-8",
                                                     "AI_CC5_SAFE_BRIDGE": "1", "AI_CC5_STEP_TEMP": str(temp)})
        started = time.monotonic()
        last = (-1, -1)
        lines = []

        def flush():
            chunk = reader.read().decode("utf-8", errors="replace")
            if chunk:
                lines.append(chunk)
                store.log(state, chunk.rstrip())

        try:
            while process.poll() is None:
                flush()
                measured = store.evidence_progress(state)
                if measured != last and measured[1] > 1:
                    store.log(state, f"หลักฐาน {measured[0]}/{measured[1]}")
                    last = measured
                if time.monotonic() - started >= timeout:
                    raise TimeoutError(f"หมดเวลารอ {timeout} วินาที")
                time.sleep(0.5)
            flush()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    if process.returncode:
        raise RuntimeError(f"exit {process.returncode}\n{''.join(lines)[-3000:]}")
    return "".join(lines)


def file_asset(path, suffix):
    return path.suffix.lower() == suffix.lower() and path.is_file() and path.stat().st_size > 4096


def manifest(store, story):
    data = load(store.root / "stories" / f"{identifier(story)}.json")
    if data is None:
        raise Blocked(f"ไม่พบเรื่อง {story}")
    return data


def select_actor(store, story, actor):
    short = actor.removeprefix(story + "_")
    key = story + "_" + identifier(short)
    cast = load(store.runs / story / "CAST_QA_INVENTORY.json", {}).get("actors", {})
    actors = manifest(store, story).get("characters", {})
    if not isinstance(actors, dict) or key not in actors:
        raise Blocked(f"ไม่มีตัวละครนี้ใน story: {actor}")
    data = actors[key]
    # New stories have no QA inventory until actors are exported; the story entry is then the source.
    if key in cast and (cast[key].get("age") != data.get("age") or cast[key].get("sex") != data.get("sex")):
        raise Blocked("อายุหรือเพศใน inventory ต่างจาก story")
    return short, f'{data["age"]} ปี ({data["age_group"]})', cast.get(key, {})


def use(store, args):
    story = identifier(args.story)
    manifest(store, story)
    run = store.runs / story
    current = store.active()
    if current and current.get("phase") in ("กำลังทำ", "ต้องตรวจ CC5"):
        raise Blocked("ตรวจงาน CC5 ที่ค้างอยู่ก่อนเปลี่ยนรอบ")
    old = load(store.state_file(story), {})
    actor, age = (None, None)
    selected_inventory = {}
    if args.actor:
        actor, age, selected_inventory = select_actor(store, story, args.actor)
    if args.donor_map and not actor:
        raise Blocked("--donor-map ต้องระบุ actor ด้วย")
    options = {}
    if args.donor_map:
        donor = args.donor_map.resolve()
        data = load(donor)
        if not isinstance(data, dict) or set(data) != {actor} or not isinstance(data[actor], dict):
            raise Blocked("donor map ต้องมี actor key เดียวและตรงกับรอบ")
        options = {"donor_map": str(donor), "donor_sha": digest(donor)}
    label = identifier(args.label) if args.label else None
    revision = (old and label and label != old["label"] and actor == old.get("actor")
                and store.step(old) and (store.step(old)[0] in ("approve", "qa")
                                       or old.get("failed_step") == store.step(old)[0]))
    switching = bool(old and actor and old.get("actor") and actor != old["actor"])
    if switching:
        # Another actor: keep the current one's progress in its own file and resume the chosen one.
        store.write(old)
        resumed = store.parked(story).get(actor)
        if resumed and not label and not options:
            resumed["finished_actors"] = sorted(store.finished_actors(old) | set(resumed.get("finished_actors", ())))
            store.write(resumed)
            save(store.runs / ".ai_cc5_active.json", {"story": story})
            store.log(resumed, f"สลับมาที่ {actor} ทำต่อจากขั้น {len(resumed['done']) + 1}")
            return
        previous, old = old, {**old, "done": [], "label": None}
    if not switching and old and store.step(old) and len(old["done"]) >= 2 and not revision:
        same = ((actor is None or actor == old["actor"])
                and (label is None or label == old["label"]) and (not options or all(
                    old.get(k) == value for k, value in options.items())))
        if not same:
            raise Blocked("รอบเดิมยังไม่เสร็จ ให้ทำต่อที่ actor และ label เดิม")
        state = old
    else:
        in_progress = old and old.get("label") and store.step(old) and not revision
        chosen_label = label or (old["label"] if in_progress else
                                 "ai_cc5_" + time.strftime("%Y%m%d") + "_" + uuid4().hex[:8])
        state = {"story": story, "actor": actor or (old.get("actor") if in_progress else None),
                 "age": age or (old.get("age") if in_progress else None), "label": chosen_label,
                 "done": old["done"] if in_progress else [], "phase": "พร้อม"}
        finished = store.finished_actors(old)
        if finished:
            state["finished_actors"] = sorted(finished)
        if chosen_label == old.get("label") and in_progress and state["actor"] == old.get("actor"):
            state.update({k: old[k] for k in ("donor_map", "donor_sha") if k in old})
        state.update(options)
        if switching and previous.get("new_actor") and not selected_inventory:
            # New-story actor (no exported QA inventory yet): face -> build flow like the queue does.
            data = manifest(store, story)["characters"][f"{story}_{actor}"]
            state.update(new_actor=True, review_tools=previous["review_tools"],
                         build_job=data.get("staging_job", f"{story}_{actor}"))
            for key in ("prior_project", "prior_project_sha"):
                if key in previous:
                    state[key] = previous[key]
        if (not in_progress or label and label != old["label"]) and (
            store.folder(state).exists() or (run / "cast_fittings" / state["label"]).exists()
        ):
            raise Blocked("label นี้มีหลักฐานเก่าอยู่แล้ว ให้เลือกชื่อใหม่")
        store.write(state)
    save(store.runs / ".ai_cc5_active.json", {"story": story})
    store.log(state, f"เลือก {story} / {state.get('actor') or 'รอ actor'} / {state['label']}")


def fitting_record(store, state):
    return load(store.fitting(state) / "look.json", {})


def target_project(store, state):
    path = Path(fitting_record(store, state).get("target", ""))
    if not file_asset(path, ".ccProject"):
        raise RuntimeError("ไม่มี .ccProject ที่บันทึกจากรอบนี้")
    return path


def validate_render(directory, source, export=False):
    evidence = load(directory / "runtime.json", {})
    expected = {"walk_00": 0, "walk_40": 24, "walk_40_side": 24, "walk_74_side": 44}
    if (evidence.get("source") != str(source) or evidence.get("source_size") != source.stat().st_size
            or evidence.get("motion_frames") != expected
            or not all(evidence.get(k) is True for k in
                       ("reopened", "motion_applied", "t_pose_applied", "review_pose_discarded"))
            or export and not evidence.get("iavatar_reopened")
            or not all(png(directory / f"{frame}.png") for frame in FRAMES)):
        raise RuntimeError(f"หลักฐาน CC5 ไม่ครบหรือไม่ตรงกับไฟล์ของรอบนี้: {directory}")
    return evidence


def review_identity(store, state, project):
    folder = store.folder(state)
    views = store.fitting(state) / "views"
    validate_render(views, project)
    return {"review_sha": digest(folder / "review.png"), "project_sha": digest(project),
            "view_sha": {frame: digest(views / f"{frame}.png") for frame in FRAMES}}


def inspect_cc5(store, state):
    from tools.cc5_build_queue import process_check

    ready, reason = process_check()
    if not ready:
        raise Blocked(f"CC5 ต้องเปิดอยู่ ตอบสนอง และบันทึกงานแล้ว ({reason})")
    guard = capture(ps(store.root / "tools/cc5_popup_guard.ps1", "-Once", "-DryRun", "-NoLog"))
    info = json.loads(capture(ps(store.root / "tools/cc5_gui.ps1", "inspect")))
    store.log(state, guard)
    store.log(state, json.dumps(info, ensure_ascii=False))
    if info.get("dialogs") or "DRYRUN " in guard or "ERROR " in guard or info.get("title", "").rstrip().endswith("*"):
        raise Blocked("พบหน้าต่างหรือการเปลี่ยนแปลงใน CC5 ให้ผู้ใช้จัดการก่อนแล้วใช้ Ai-cc5 log")


def diagnostics(store, state, temp, exc):
    folder = store.folder(state)
    report = {"time": stamp(), "seconds": round(time.time() - state["started"], 2),
              "step": store.step(state)[0], "error": str(exc), "uia": "", "ocr": "", "screenshot": ""}
    gui = store.root / "tools/cc5_gui.ps1"
    try:
        report["uia"] = capture(ps(gui, "inspect"))
    except Exception as error:
        report["uia"] = str(error)
    try:
        fail = folder / "last_fail.png"
        probe = temp / "ocr.png"
        try:
            capture(ps(gui, "shot", probe))
            if not png(probe):
                raise RuntimeError("ภาพ FAIL ไม่สมบูรณ์")
            atomic(fail, probe.read_bytes())
            report["screenshot"] = str(fail)
            report["ocr"] = capture(ps(store.root / "tools/ai_cc5_ocr.ps1", probe), timeout=30)
        finally:
            probe.unlink(missing_ok=True)
    except Exception as error:
        report["ocr"] = report["ocr"] or str(error)
    save(folder / "last_fail.json", report)


def run_action(store, state, temp, key):
    story = state["story"]
    run = store.runs / story
    actor = state.get("actor")
    folder = store.folder(state)
    fit = store.fitting(state) if actor else None

    def command(script, *args, timeout=240):
        return run_step_command(store, state, temp, python(script, *args), timeout)

    if state.get("new_actor") and key in {"select", "open", "fit", "render", "sheet"}:
        from ai_cc5_continue import new_actor_action

        new_actor_action(store, state, temp, key)
        return

    if key == "preflight":
        result = command(store.root / "tools/cc5_production_preflight.py", "--story", story,
                         "--runtime", timeout=45)
        if "BLOCKED" in result or "READY_FOR_NEXT_GATE" not in result:
            raise RuntimeError("preflight ไม่มีผล READY_FOR_NEXT_GATE")
    elif key == "select":
        if not actor:
            raise Blocked("ใช้ Ai-cc5 use <story> <actor> ตามลำดับจากผู้ใช้")
        missing = [name for name in NEEDED if not (run / name).is_file()]
        if missing:
            raise Blocked("เรื่องนี้ยังไม่มี recipe สำหรับพรีวิว: " + ", ".join(missing))
        _, _, selected = select_actor(store, story, actor)
        source = Path(selected["chosen"]["project"])
        if state.get("donor_map"):
            donor = Path(state["donor_map"])
            if digest(donor) != state["donor_sha"]:
                raise Blocked("donor map เปลี่ยนหลังเลือก")
            prior = load(donor)[actor].get("source_fitting")
            if prior:
                source = Path(load(run / "cast_fittings" / identifier(prior) / actor / "look.json")["target"])
        if not file_asset(source, ".ccProject"):
            raise Blocked("ไม่พบ .ccProject ต้นฉบับของช่วงวัยที่เลือก")
        state["source"] = str(source)
        state["source_sha"] = digest(source)
    elif key == "open":
        source = Path(state["source"])
        if digest(source) != state["source_sha"]:
            raise Blocked("ไฟล์ต้นฉบับเปลี่ยนหลังเลือก")
        with lock(store.runs / ".cc5_global_production_flow.lock"):
            evidence = command(run / "qa_bridge.py", "cc5/probes/open_path.py", f"path={source}",
                               "verify_textures=1", f"texture_module_dir={store.root / 'cc5'}")
        data = json.loads(evidence.strip().splitlines()[-1])
        if data.get("source") != str(source) or not data.get("reopened") or data.get("texture_check_frames", 0) < 2:
            raise RuntimeError("ยืนยันการเปิดโปรเจกต์และ texture ไม่ได้")
        save(folder / "open.json", data)
    elif key == "fit":
        if digest(Path(state["source"])) != state["source_sha"]:
            raise Blocked("ไฟล์ต้นฉบับเปลี่ยนหลังเปิด")
        mode = ("--fit", actor)
        if state.get("donor_map"):
            donor = Path(state["donor_map"])
            if digest(donor) != state["donor_sha"]:
                raise Blocked("donor map เปลี่ยนหลังเลือก")
            mode = ("--donor-map", donor)
        command(run / "review_cast.py", *mode, "--label", state["label"], "--fit-only",
                "--expected-source", state["source"])
        target_project(store, state)
        if Path(fitting_record(store, state)["source"]).resolve() != Path(state["source"]).resolve():
            raise RuntimeError("รอบลองชุดใช้ต้นฉบับคนละไฟล์กับขั้นเปิดงาน")
    elif key == "render":
        project = target_project(store, state)
        command(run / "review_cast.py", "--render-reviewed", actor, "--label", state["label"], "--exact")
        validate_render(fit / "views", project)
    elif key == "sheet":
        project = target_project(store, state)
        validate_render(fit / "views", project)
        review = folder / "review.png"
        _, _, selected = select_actor(store, story, actor)
        preview = temp / "review.png"
        command(run / "make_actor_review.py", fit / "views", selected["name"], preview, timeout=45)
        if not png(preview):
            raise RuntimeError("make_actor_review ไม่ได้สร้าง PNG ที่อ่านได้")
        atomic(review, preview.read_bytes())
        state["review"] = review_identity(store, state, project)
    elif key == "send":
        from tools.cc5_production_flow import ntfy_send

        project = target_project(store, state)
        if review_identity(store, state, project) != state["review"]:
            raise Blocked("รูปหรือโปรเจกต์เปลี่ยนหลังจัดภาพรวม")
        review = folder / "review.png"
        sha = state["review"]["review_sha"]
        receipt_key = f"{story}_{actor}/preview/{sha}"
        path = run / "flow_ntfy_receipts.json"

        def receipt():
            item = load(path, {}).get("sent", {}).get(receipt_key, {})
            return item if item.get("id") and item.get("hash") == sha else None

        item = receipt()
        if not item:
            attempt = run / "ai_cc5" / "delivery" / f"{sha}.json"
            if attempt.exists():
                raise Blocked("เคยส่งภาพนี้แล้วแต่ไม่มีใบยืนยัน ตรวจ Pic-Gptz ก่อนส่งอีกครั้ง")
            save(attempt, {"time": stamp(), "hash": sha})
            ok, message = ntfy_send(store.root / "stories" / f"{story}.json",
                                    f"{story}_{actor}", "preview", review, run)
            store.log(state, message)
            item = receipt()
            if not ok or not item:
                raise RuntimeError(f"ไม่ได้ใบยืนยัน Pic-Gptz: {message}")
        state["delivery"] = {"id": item["id"], "sha": sha, "recorded": utc_now()}
    elif key == "export":
        project = target_project(store, state)
        if not state.get("approval") or review_identity(store, state, project) != state["review"]:
            raise Blocked("โปรเจกต์และภาพต้องตรงกับรอบที่ผู้ใช้อนุมัติ")
        avatar = project.with_suffix(".iAvatar")
        if state.get("new_actor"):
            import kit
            production = kit.load_story(story)
            actor_data = production["characters"][f"{story}_{actor}"]
            output_root = Path(production["out_dir"]).resolve()
            output = (output_root / actor_data.get("folder", "")).resolve()
            if not output.is_relative_to(output_root):
                raise Blocked("โฟลเดอร์ส่งออกอยู่นอกงานของเรื่อง")
            output.mkdir(parents=True, exist_ok=True)
            avatar = output / f'{actor_data["name"]}.iAvatar'
            if state.get("color_revision"):
                state["color_delivery_target"] = str(avatar)
                output = project.parent
                avatar = project.with_suffix(".iAvatar")
            if avatar.exists() and state.get("export_path") != str(avatar):
                raise Blocked("มีไฟล์ส่งออกชื่อนี้อยู่แล้ว")
            state["export_path"] = str(avatar)
            store.write(state)
            recipe = store.root / state["review_tools"]
            with lock(store.runs / ".cc5_global_production_flow.lock"):
                if not avatar.exists():
                    command(recipe / "qa_bridge.py", str(recipe / "qa_export_fitting.py"),
                            f"source={project}", f"target={avatar}", f"delivery_dir={output}")
                if not (fit / "export_check").exists():
                    view_report = load(fit / "views" / "runtime.json", {})
                    templates = Path(kit.CFG.get("cc5_animation") or
                                     Path.home().parent / "Public/Documents/Reallusion/Reallusion Templates/Animation")
                    command(recipe / "qa_bridge.py", str(recipe / "qa_cast_runtime.py"),
                            f"path={avatar}", f"out={fit / 'export_check'}",
                            f"motion={view_report['motion_path']}", f"pose={templates / 'Pose/Calibration/T-Pose.rlPose'}")
        else:
            command(run / "review_cast.py", "--export-reviewed", actor, "--label", state["label"], "--exact",
                    timeout=420)
        if not file_asset(avatar, ".iAvatar"):
            raise RuntimeError("ไม่มี iAvatar ที่ใช้งานได้")
        validate_render(fit / "export_check", avatar, export=True)
        state["export_sha"] = digest(avatar)
        state["export_view_sha"] = {name: digest(fit / "export_check" / f"{name}.png") for name in FRAMES}
        qa_file = folder / "qa.json"
        if not qa_file.exists():
            save(qa_file, {"review_sha": state["review"]["review_sha"], "avatar_sha": state["export_sha"],
                           "checks": {q: {"result": "", "evidence": ""} for q in QA_KEYS}})
    elif key == "qa":
        qa = load(folder / "qa.json", {})
        checks = qa.get("checks", {})
        if not all(check_record(checks.get(q)) for q in QA_KEYS):
            raise Blocked(f"ดูภาพจริงและกรอกผลพร้อมหลักฐานทั้ง Q01–Q10 ใน {folder / 'qa.json'}")
        if any(checks[q]["result"] != "PASS" for q in QA_KEYS):
            raise RuntimeError("QA มีข้อที่เป็น FIX หรือ REVIEW")
        project = target_project(store, state)
        avatar = Path(state.get("export_path") or project.with_suffix(".iAvatar"))
        if (review_identity(store, state, project) != state["review"]
                or qa.get("review_sha") != state["review"]["review_sha"]
                or qa.get("avatar_sha") != state["export_sha"]
                or digest(avatar) != state["export_sha"]):
            raise RuntimeError("หลักฐาน QA เปลี่ยนจากรอบที่ตรวจ")
        validate_render(fit / "export_check", avatar, export=True)
        if any(digest(fit / "export_check" / f"{name}.png") != expected
               for name, expected in state["export_view_sha"].items()):
            raise RuntimeError("ภาพเปิด iAvatar กลับเปลี่ยนจากรอบที่ส่งออก")
        state["qa_sha"] = digest(folder / "qa.json")
    elif key == "tidy":
        if digest(folder / "qa.json") != state["qa_sha"]:
            raise Blocked("QA เปลี่ยนหลังผ่านการตรวจ")
        project = target_project(store, state)
        avatar = Path(state.get("export_path") or project.with_suffix(".iAvatar"))
        if digest(avatar) != state["export_sha"]:
            raise Blocked("iAvatar เปลี่ยนหลังผ่านการตรวจ")
        if state.get("color_revision"):
            from ai_cc5_continue import publish_color_revision
            publish_color_revision(store, state, avatar)
            return
        from tools.job_tidy import tidy
        import kit

        jobs = Path(kit.JOBS).resolve()
        source = (project if state.get("new_actor") else Path(state["source"])).resolve()
        job_dir = jobs / state.get("build_job", f"{story}_{actor}")
        if source.parent != job_dir or job_dir.resolve() != job_dir:
            store.log(state, "ต้นฉบับไม่ได้อ้าง staging ของ actor นี้ จึงไม่มี staging ที่ยืนยันได้ให้ tidy")
            return
        with lock(store.runs / ".cc5_global_production_flow.lock"):
            job = load(job_dir / "job.json", {})
            result = job_dir / "result.txt"
            if not job.get("name") or not result.is_file() or source.stem != job["name"]:
                raise Blocked("หลักฐาน build ของ staging ไม่ครบ")
            lines = result.read_text(encoding="utf-8-sig").splitlines()
            if any("FAIL" in line for line in lines):
                raise Blocked("build มี FAIL เก็บ staging ไว้")
            if not any(re.match(r"OK\s+save\s+\(", line) for line in lines):
                raise Blocked("ไม่มีหลักฐาน save สำเร็จใน result.txt")
            store.log(state, tidy(str(job_dir), job, job["name"], lines))


def confirmed_chat(quote, after, sessions=None, thread=None):
    thread = thread or os.environ.get("CODEX_THREAD_ID")
    try:
        UUID(thread or "")
    except ValueError as exc:
        raise Blocked("ต้องบันทึกจากแชต Codex ที่ผู้ใช้พิมพ์ข้อความอนุมัติ") from exc
    if not re.fullmatch(
        r"(?:อนุมัติ|ผ่าน|โอเค|ตกลง|ส่งออกได้|approved?|yes)"
        r"(?:\s*(?:ให้ส่งออก|ส่งออกได้|ครับ|ค่ะ|คะ|เลย))*[.!ฯ]*",
        quote.strip(), flags=re.IGNORECASE,
    ):
        raise Blocked("ต้องใช้ข้อความอนุมัติที่ชัดเจนจากผู้ใช้ เช่น อนุมัติ")
    directory = sessions or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    for path in directory.rglob(f"rollout-*-{thread}.jsonl"):
        latest = None
        with path.open(encoding="utf-8") as stream:
            for raw in stream:
                try:
                    entry = json.loads(raw)
                except ValueError:
                    continue
                payload = entry.get("payload", {})
                if (entry.get("type") == "response_item" and payload.get("type") == "message"
                        and payload.get("role") == "user"):
                    messages = [part["text"] for part in payload["content"] if part.get("type") == "input_text"]
                    if messages:
                        latest = (messages[-1], entry.get("timestamp", ""))
        if latest and latest[0] == quote and (
            datetime.fromisoformat(latest[1]) > datetime.fromisoformat(after)
        ):
            return {"said": quote, "thread": thread, "chat_timestamp": latest[1]}
    raise Blocked("ไม่พบข้อความผู้ใช้ที่ตรงทุกตัวอักษรในแชตนี้หลังส่งภาพ")


def complete(store, state, key):
    state.pop("failed_step", None)
    state["done"].append(key)
    if key == STEPS[-1][0]:
        state["finished_actors"] = sorted(store.finished_actors(state))
    state["phase"] = "รอผู้ใช้" if key == "send" else "พร้อม"
    store.write(state)
    store.log(state, f"OK {key} · ขั้นนี้ 100%")


def approve(store, state, quote):
    if not store.step(state) or store.step(state)[0] != "approve" or not state.get("delivery"):
        raise Blocked("บันทึกอนุมัติได้เมื่อส่งภาพของรอบนี้และได้ใบยืนยันแล้ว")
    project = target_project(store, state)
    if review_identity(store, state, project) != state["review"]:
        raise Blocked("ภาพหรือโปรเจกต์เปลี่ยนหลังส่ง")
    state["approval"] = confirmed_chat(quote, state["delivery"]["recorded"])
    store.log(state, f'ได้รับอนุมัติจากแชต: {quote}')
    complete(store, state, "approve")


def next_command(store, state):
    if not state:
        return "Ai-cc5 use <story> [actor]"
    if store.story_is_draft(state["story"]) and not state.get("new_actor"):
        return "Ai-cc5 prepare"
    step = store.step(state)
    if not step:
        return "Ai-cc5 status"
    if state.get("phase") in ("กำลังทำ", "ต้องตรวจ CC5"):
        return "Ai-cc5 log"
    if step[0] == "select" and not state.get("actor"):
        return f'Ai-cc5 use {state["story"]} <actor>'
    if step[0] == "approve":
        return 'Ai-cc5 approve --said "<ข้อความจริงจากผู้ใช้>"'
    if step[0] in LIVE:
        return "Ai-cc5 do --dry"
    return "Ai-cc5 do"


def do(store, state, args):
    if store.story_is_draft(state["story"]) and not state.get("new_actor"):
        print("เรื่องนี้อยู่ในขั้นเตรียมเรื่อง · ใช้ Ai-cc5 prepare")
        return 0 if args.dry else 2
    step = store.step(state)
    if not step:
        print("ตัวละครรอบนี้เสร็จแล้ว")
        return 0
    key, title, _, rule = step
    if key in ("render", "send"):
        pending_garment = flow_preview.pending_before_review(store, state)
        if pending_garment is not None:
            message = f"งานชุดยังค้างขั้น {pending_garment}/{len(flow_preview.STEPS)} · ดูด้วย Ai-cc5 garment next"
            if args.dry:
                print(message)
                return 0
            raise Blocked(message)
    if args.dry:
        print(f"ขั้น {len(state['done']) + 1} {title} · {rule}")
        if key in LIVE:
            print("เมื่อผู้ใช้อนุญาตให้ทำขั้นนี้ ใช้ Ai-cc5 do --allow-cc5")
        elif key == "approve":
            print(next_command(store, state))
        return 0
    if state.get("phase") in ("กำลังทำ", "ต้องตรวจ CC5"):
        raise Blocked("งานก่อนหน้าหยุดระหว่างรอผล CC5 ตรวจ Ai-cc5 log และยืนยันว่าไม่มีงานค้างก่อนใช้ do --recover")
    if key == "approve":
        raise Blocked(next_command(store, state))
    if key in LIVE and not args.allow_cc5:
        raise Blocked(f"{title} · {rule}\nเมื่อผู้ใช้อนุญาต ใช้ Ai-cc5 do --allow-cc5")
    state.update(phase="กำลังทำ", started=time.time())
    store.write(state)
    store.log(state, f"เริ่ม {key} · {rule}")
    with TemporaryDirectory(prefix="ai-cc5-") as workspace:
        temp = Path(workspace)
        try:
            if key in LIVE and not (state.get("new_actor") and key == "open"):
                inspect_cc5(store, state)
            run_action(store, state, temp, key)
        except Blocked as exc:
            state["phase"] = "รอตรวจข้อมูล"
            store.write(state)
            store.log(state, f"รอ: {exc}")
            raise
        except Exception as exc:
            state["failed_step"] = key
            if key in LIVE and not (state.get("new_actor") and key == "open"):
                state["phase"] = "ต้องตรวจ CC5"
            else:
                state["phase"] = "FAIL"
            store.write(state)
            store.log(state, f"FAIL {key}: {exc}")
            diagnostics(store, state, temp, exc)
            print(f"FAIL {key} · ดู Ai-cc5 log", file=sys.stderr)
            return 1
    complete(store, state, key)
    print(store.snapshot()[1])
    return 0


def recover(store, state):
    step = store.step(state)
    if state.get("phase") not in ("กำลังทำ", "ต้องตรวจ CC5"):
        raise Blocked("ไม่มีขั้นที่ค้าง")
    if step and step[0] in LIVE:
        inspect_cc5(store, state)
        import kit
        bridge = Path(kit.JOBS) / "bridge"
        heartbeat = bridge / "heartbeat.txt"
        if (not heartbeat.is_file() or time.time() - heartbeat.stat().st_mtime > 5
                or any((bridge / "inbox").glob("*.json"))):
            raise Blocked("ยังยืนยันไม่ได้ว่าบริดจ์ CC5 ว่าง")
    state["phase"] = "พร้อม"
    store.write(state)
    store.log(state, "ยืนยันขั้นที่ค้างแล้ว พร้อมตรวจซ้ำตามหลักฐานเดิม")


def doctor(store):
    import kit

    cc5 = kit.CFG.get("cc5")
    if not cc5:
        cc5 = Path(os.environ.get("ProgramFiles", Path.home())) / "Reallusion/Character Creator 5/Bin64/CharacterCreator.exe"
    blender = Path(kit.BLENDER)
    if not blender.is_file():
        found = shutil.which("blender")
        if not found:
            install_root = Path(os.environ.get("ProgramFiles", Path.home())) / "Blender Foundation"
            installed = [path for path in install_root.glob("Blender */blender.exe") if path.is_file()]
            found = max(installed, key=lambda path: tuple(map(int, re.findall(r"\d+", path.parent.name))),
                        default=None)
        if found:
            blender = Path(found)
    checks = (
        ("CC5", Path(cc5), Path(cc5).is_file()),
        ("Python", Path(sys.executable), sys.version_info >= (3, 11)),
        ("Blender", blender, blender.is_file()),
        ("Tidmunz Studio", Path(kit.PROGRAM), (Path(kit.PROGRAM) / "snapgen_gui_v2.py").is_file()),
        ("คลังเสื้อผ้า", Path(kit.LIB), Path(kit.LIB).is_dir()),
        ("cc5_jobs", Path(kit.JOBS), Path(kit.JOBS).is_dir()),
    )
    for label, path, ok in checks:
        print(f'{"OK" if ok else "MISSING":7} {label}  {path}')
    return 0 if all(ok for _, _, ok in checks) else 2


def main(argv=None, root=ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    parser = argparse.ArgumentParser(prog="Ai-cc5")
    commands = parser.add_subparsers(dest="command")
    for name in ("status", "steps", "prepare", "log", "doctor", "window", "update", "version"):
        commands.add_parser(name)
    select = commands.add_parser("use")
    select.add_argument("story")
    select.add_argument("actor", nargs="?")
    select.add_argument("--label")
    select.add_argument("--donor-map", type=Path)
    execute = commands.add_parser("do")
    flags = execute.add_mutually_exclusive_group()
    flags.add_argument("--dry", action="store_true")
    flags.add_argument("--allow-cc5", action="store_true")
    flags.add_argument("--recover", action="store_true")
    commands.add_parser("rules").add_argument("step")
    commands.add_parser("approve").add_argument("--said", required=True)
    flow_preview.add_cli(commands.add_parser("garment"))
    args = parser.parse_args(argv)
    store = State(root)
    cmd = args.command
    try:
        if cmd == "garment":
            return flow_preview.cli(store, args)
        if cmd not in ("update",) and not (cmd == "do" and args.dry):
            try:
                with lock(store.runs / ".ai_cc5_update.lock"):
                    notice, _ = ai_cc5_update.check(root)
                if notice and cmd != "status":
                    print(notice, file=sys.stderr)
            except (Blocked, OSError, ValueError):
                pass
        if cmd in ("use", "approve", "update") or cmd == "do" and not args.dry:
            with lock(store.runs / ".ai_cc5.lock"):
                state = store.active()
                if cmd == "update":
                    if state.get("phase") in ("กำลังทำ", "ต้องตรวจ CC5"):
                        raise Blocked("ตรวจงานที่ค้างก่อนอัปเดต")
                    with lock(store.runs / ".ai_cc5_update.lock"):
                        notice, ok = ai_cc5_update.check(root, explicit=True)
                    print(notice)
                    return 0 if ok else 2
                if cmd == "use":
                    use(store, args)
                    print(store.snapshot()[1])
                elif not state:
                    raise Blocked(next_command(store, state))
                elif cmd == "approve":
                    approve(store, state, args.said)
                    print(store.snapshot()[1])
                elif args.recover:
                    recover(store, state)
                else:
                    return do(store, state, args)
            return 0
        if cmd == "doctor":
            return doctor(store)
        if cmd == "version":
            print(ai_cc5_update.version(root))
            return 0
        if cmd == "window":
            from ai_cc5_progress import show
            show(store)
            return 0
        if cmd in ("steps", "rules"):
            count = 0
            for index, (key, label, owner, rule) in enumerate(STEPS, start=1):
                if cmd == "steps" or args.step in {str(index), key, label}:
                    print(f"{index:02d} {key} · {label} · {owner}" + (f"\n{rule}" if cmd == "rules" else ""))
                    count += 1
            if count == 0:
                raise Blocked("ไม่พบขั้น ใช้ Ai-cc5 steps")
            return 0
        state, summary = store.snapshot()
        if cmd == "do":
            if not state:
                raise Blocked(next_command(store, state))
            return do(store, state, args)
        if cmd == "prepare":
            if not state:
                raise Blocked(next_command(store, state))
            rows, gate = store.preparation(state["story"])
            print(store.preparation_folder(state["story"]))
            for index, (name, path, status) in enumerate(rows, 1):
                print(f"{index}. {name} · {status} · {path.name}")
            for error in gate.get("errors", ()):
                print(error)
            return 0
        if cmd is None:
            print("Ai-cc5 · พรีวิวตัวละคร CC5 ทีละตัวและช่วงวัย")
            print("use เลือกงาน · steps ดูขั้น · do --dry ดูก่อนลงมือ · log ดูผล · window เปิดหน้าต่าง")
        print(summary)
        if cmd == "log":
            print(store.log_view(state))
        if cmd is None:
            print(f"คำสั่งถัดไป  {next_command(store, state)}")
        return 0
    except (Blocked, OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
