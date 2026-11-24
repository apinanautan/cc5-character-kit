"""Run a user's Preview approval through delivery and the next prepared actor."""

import argparse
import re
from pathlib import Path
from uuid import uuid4

from ai_cc5_state import FRAMES, QA_KEYS, Blocked, ROOT, State, digest, load, lock, save, utc_now

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ai_cc5


def approval_ready(store, state):
    delivery = state.get("delivery", {})
    review = state.get("review", {})
    step = store.step(state) if state else None
    return bool(step and step[0] == "approve" and delivery.get("id") and review.get("review_sha")
                and delivery.get("sha") == review["review_sha"]
                and (store.folder(state) / "review.png").is_file())


def approval_identity(state):
    return state.get("story"), state.get("label"), state.get("delivery", {}).get("id")


def approve_click(store, shown):
    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active()
        if approval_identity(state) != approval_identity(shown) or not approval_ready(store, state):
            raise Blocked("รอบพรีวิวเปลี่ยนแล้ว เปิดภาพของรอบปัจจุบันก่อน")
        project = ai_cc5.target_project(store, state)
        if ai_cc5.review_identity(store, state, project) != state["review"]:
            raise Blocked("ภาพหรือโปรเจกต์เปลี่ยนหลังส่ง")
        state["approval"] = {
            "origin": "preview_button", "at": utc_now(),
            "receipt": state["delivery"]["id"], "review_sha": state["review"]["review_sha"],
        }
        state["continuation"] = {"token": uuid4().hex, "status": "queued"}
        ai_cc5.complete(store, state, "approve")
        store.log(state, "ผู้ใช้กดอนุมัติใน Preview · อนุญาตส่งออกและเริ่มตัวถัดไปหนึ่งตัว")
        return state["continuation"]["token"]


def compare_reopened_views(before, after):
    from PIL import Image, ImageChops

    rates = {}
    for name in FRAMES:
        with Image.open(before / f"{name}.png") as approved, Image.open(after / f"{name}.png") as reopened:
            if approved.size != reopened.size:
                raise Blocked(f"ขนาดภาพเปิดกลับต่างจากภาพที่อนุมัติในมุม {name}")
            width, height = approved.size
            box = ((0, 0, width, height) if name.startswith("t_") else
                   (width // 4, 0, width * 3 // 4, height))
            expected = approved.crop(box).convert("RGB").resize((180, 180), Image.Resampling.LANCZOS)
            actual = reopened.crop(box).convert("RGB").resize((180, 180), Image.Resampling.LANCZOS)
            diff = ImageChops.difference(expected, actual)
            red, green, blue = diff.split()
            strongest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
            rate = sum(strongest.histogram()[25:]) / (180 * 180)
        rates[name] = round(rate, 5)
        if rate > .025:
            raise Blocked(f"ภาพ {name} หลังเปิด iAvatar เปลี่ยน {rate:.1%} ให้ตรวจภาพก่อนเก็บงาน")
    return rates


def verified_qa(store, state):
    folder = store.folder(state)
    fit = store.fitting(state)
    path = folder / "qa.json"
    qa = load(path, {})
    if all(check.get("result") for check in qa.get("checks", {}).values()) and qa.get("checks"):
        return
    approval = state["approval"]
    if approval["review_sha"] != state["review"]["review_sha"] or approval["receipt"] != state["delivery"]["id"]:
        raise Blocked("ใบอนุมัติไม่ตรงกับภาพของรอบนี้")
    project = ai_cc5.target_project(store, state)
    avatar = Path(state.get("export_path") or project.with_suffix(".iAvatar"))
    evidence = ai_cc5.validate_render(fit / "export_check", avatar, export=True)
    original = ai_cc5.validate_render(fit / "views", project)
    if not original.get("polygon_counts") or any(original.get(key) != evidence.get(key)
                                                  for key in ("clothes", "hair", "polygon_counts")):
        raise Blocked("รายการชุด ผมหรือจำนวนโพลิกอนหลังเปิดกลับต่างจากภาพที่อนุมัติ")
    if not original.get("clothes"):
        raise Blocked("ไม่มีหลักฐานชุดบนตัวละคร")
    rates = compare_reopened_views(fit / "views", fit / "export_check")
    actor_id = f'{state["story"]}_{state["actor"]}'
    actor = store.story_manifest(state["story"])["characters"][actor_id]
    identity = ai_cc5.review_identity(store, state, project)
    if identity != state["review"] or digest(avatar) != state["export_sha"]:
        raise Blocked("ไฟล์หรือภาพเปลี่ยนหลังส่งออก")
    polygons = sum(evidence["polygon_counts"].values())
    receipt = approval["receipt"]
    approved_note = f"ผู้ใช้ตรวจและกดอนุมัติภาพจริง {receipt}"
    reference = {
        "Q01": f'{actor["name"]} · {actor["age"]} ปี ตาม manifest และ{approved_note}',
        "Q02": f'ช่วงวัย {actor.get("age_group")} ฐาน {actor.get("body", "ตามไฟล์ต้นฉบับ")} จาก manifest และภาพเต็มตัวที่อนุมัติ',
        "Q03": f"{approved_note} · โมเดลเปิดกลับยังมีผม {', '.join(evidence['hair'])}",
        "Q04": f"{approved_note} · ชุดรอบตรวจ {', '.join(evidence['clothes'])}",
        "Q05": f"{approved_note} · ตรวจเทียบรูปทรงหน้า ข้าง หลัง และ T-Pose หลังเปิดกลับ",
        "Q06": f"{approved_note} · เทียบชุดช่วงเคลื่อนไหวทั้งเฟรม 0/24/44 หลังเปิดกลับ",
        "Q07": f"{approved_note} · สี พื้นผิว และเส้นตะเข็บเทียบจากภาพที่เปิดกลับ",
        "Q08": f"CC5 รายงาน {polygons:,} โพลิกอน · จำนวนเท่าก่อนส่งออก · ใช้รายละเอียดตามภาพที่ผู้ใช้อนุมัติสำหรับเรนเดอร์",
        "Q09": f"{avatar.name} {avatar.stat().st_size:,} ไบต์ · ยืนยัน SHA-256 ของไฟล์และภาพ",
        "Q10": "CC5 เปิด .iAvatar กลับและเรนเดอร์ตรวจครบ · องค์ประกอบและจำนวนโพลิกอนตรงกับไฟล์ที่อนุมัติ",
    }
    qa.update(review_sha=identity["review_sha"], avatar_sha=state["export_sha"],
              checks={key: {"result": "PASS", "evidence": reference[key]} for key in QA_KEYS},
              reopened_image_mismatch=rates, approved_preview=receipt, polygon_counts=evidence["polygon_counts"])
    save(path, qa)


def next_ready_actor(store, state):
    from argparse import Namespace

    slug = state["story"]
    manifest = store.story_manifest(slug)
    actors = manifest.get("characters", {})
    order = manifest.get("production_queue", list(actors))
    finished = store.finished_actors(state)
    key = next((key for key in order if key in actors and key not in finished), None)
    if not key:
        if manifest.get("cast_brief") and not manifest.get("cast_finalized"):
            store.log(state, "ตัวปัจจุบันเสร็จแล้ว · ยังไม่มีตัวถัดไปที่ล็อกข้อมูลผลิตไว้")
        return None
    short = key.removeprefix(slug + "_")
    if state.get("color_revision"):
        plan = Path(state["color_revision"]).parent.parent / short / "plan.json"
        if plan.is_file():
            prepared = load(plan.parent / "queued_state.json", {})
            if prepared:
                if prepared.get("actor") != short or prepared.get("color_revision") != str(plan):
                    raise Blocked("คิวแก้สีไม่ตรงตัวละคร")
                fresh = prepared
                fresh["finished_actors"] = sorted(finished)
            else:
                fresh = color_revision_state(store, state, plan, finished)
            store.write(fresh)
            store.log(fresh, "ต่อคิวแก้สีเสื้อบนโมเดลเดิม")
            return fresh
    if not state.get("new_actor"):
        ai_cc5.use(store, Namespace(story=slug, actor=short, donor_map=None, label=None))
        return store.active()
    from tools.cc5_wardrobe_lock import locked_look

    actor = actors[key]
    locked_look(manifest, key, actor)
    current_project = ai_cc5.target_project(store, state)
    fresh = {
        "story": slug, "actor": short, "age": f'{actor["age"]} ปี',
        "label": "ai_cc5_" + uuid4().hex[:12], "new_actor": True, "review_tools": state["review_tools"],
        "phase": "พร้อม", "done": [], "finished_actors": sorted(finished),
        "prior_project": str(current_project), "prior_project_sha": digest(current_project),
        "build_job": actor.get("staging_job", key),
    }
    store.write(fresh)
    store.log(fresh, f'เริ่มตัวถัดไป {actor["name"]} อายุ {actor["age"]} ปี ตามคิว')
    return fresh


def run_continuation(store, token):
    from argparse import Namespace

    args = Namespace(dry=False, allow_cc5=True)
    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active()
        record = state.get("continuation", {})
        if record.get("token") != token or record.get("status") != "queued":
            raise Blocked("ไม่มีคิวต่อจากปุ่มอนุมัติของรอบนี้")
        record["status"] = "running"
        store.write(state)
        current = state
        try:
            while step := store.step(current):
                if step[0] == "approve" and current.get("finish_request"):
                    finish_approval(store, current)
                    continue
                if step[0] == "qa":
                    verified_qa(store, current)
                if ai_cc5.do(store, current, args):
                    raise Blocked(f"หยุดที่ขั้น {step[1]} · เปิดบันทึกงานเพื่อดูสาเหตุ")
            record["status"] = "complete"
            store.write(current)
            next_state = next_ready_actor(store, current)
            if next_state is None:
                return 0
            current = next_state
            while step := store.step(current):
                if step[0] == "approve":
                    if current.get("finish_request"):
                        finish_approval(store, current)
                        continue
                    break
                if ai_cc5.do(store, current, args):
                    raise Blocked(f"ตัวถัดไปหยุดที่ขั้น {step[1]} · เปิดบันทึกงาน")
            return 0
        except (Blocked, OSError, KeyError, ValueError, RuntimeError) as error:
            if current is state and record["status"] != "complete":
                record["status"] = "blocked"
            if current.get("phase") not in ("FAIL", "ต้องตรวจ CC5"):
                current["phase"] = "รอตรวจข้อมูล"
            store.write(current)
            store.log(current, f"หยุดการทำต่อ: {error}")
            return 2


def finish_approval(store, state):
    request = state.get("finish_request", {})
    delivery = state.get("delivery", {})
    review = state.get("review", {})
    if (request.get("said") != "ทำต่อให้เสร็จ" or not delivery.get("id")
            or delivery.get("sha") != review.get("review_sha")):
        raise Blocked("คำสั่งทำต่อหรือหลักฐานภาพรีวิวไม่ตรงกับรอบนี้")
    project = ai_cc5.target_project(store, state)
    if ai_cc5.review_identity(store, state, project) != review:
        raise Blocked("ภาพหรือโปรเจกต์เปลี่ยนหลังได้คำสั่งทำต่อ")
    state["approval"] = {
        "origin": "user_finish_instruction", "said": request["said"],
        "at": request["at"], "receipt": delivery["id"], "review_sha": review["review_sha"],
    }
    ai_cc5.complete(store, state, "approve")


def resume_after_import_failure(store):
    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active()
        record = state.get("continuation", {})
        failure = load(store.folder(state) / "last_fail.json", {})
        step = store.step(state)
        if (record.get("status") != "blocked" or state.get("phase") != "พร้อม"
                or not step or step[0] != "export" or state.get("failed_step") != "export"
                or failure.get("step") != "export" or failure.get("error") != "No module named 'tools'"):
            raise Blocked("resume ได้เฉพาะ export ที่หยุดก่อนสั่ง CC5 เพราะ import tools ไม่พบ")
        approval = state.get("approval", {})
        delivery = state.get("delivery", {})
        review = state.get("review", {})
        if (approval.get("origin") != "preview_button" or approval.get("receipt") != delivery.get("id")
                or approval.get("review_sha") != review.get("review_sha")
                or delivery.get("sha") != review.get("review_sha")):
            raise Blocked("ใบอนุมัติไม่ตรงกับภาพและใบยืนยันของรอบนี้")
        project = ai_cc5.target_project(store, state)
        avatar = Path(state.get("export_path") or project.with_suffix(".iAvatar"))
        if avatar.exists() or (store.fitting(state) / "export_check").exists():
            raise Blocked("พบไฟล์ส่งออกหรือหลักฐานบางส่วน ตรวจด้วยมือก่อนลองซ้ำ")
        record["status"] = "queued"
        store.write(state)
        store.log(state, "กู้ต่อจาก import error ที่เกิดก่อนสั่ง CC5 · ตรวจแล้วว่าไม่มีไฟล์ส่งออกค้าง")
        token = record["token"]
    return run_continuation(store, token)


def resume_corrected_fit(store):
    with lock(store.runs / ".ai_cc5.lock"):
        state = store.active()
        record = state.get("continuation")
        if not record:
            record = {"token": uuid4().hex, "status": "blocked"}
            state["continuation"] = record
        failure = load(store.folder(state) / "last_fail.json", {})
        step = store.step(state)
        if (record.get("status") != "blocked" or state.get("phase") != "พร้อม"
                or not step or step[0] != "fit" or state.get("failed_step") != "fit"
                or failure.get("step") != "fit"
                or failure.get("error") != "ผล Headshot หรือชุดของตัวถัดไปยังตรวจไม่ผ่าน"
                or not state.get("new_actor")
                or state.get("finish_request", {}).get("said") != "ทำต่อให้เสร็จ"):
            raise Blocked("resume ได้เฉพาะขั้น fit ของตัวถัดไปที่ตรวจแล้วและผู้ใช้สั่งทำต่อ")
        job = state.get("build_job")
        if not job or (Path(__import__("kit").JOBS) / job).exists():
            raise Blocked("มี staging ของ build แก้ไขอยู่แล้ว ตรวจผลเดิมก่อนเริ่มซ้ำ")
        locked_look = __import__("tools.cc5_wardrobe_lock", fromlist=["locked_look"]).locked_look
        manifest = store.story_manifest(state["story"])
        actor_key = f'{state["story"]}_{state["actor"]}'
        locked_look(manifest, actor_key, manifest["characters"][actor_key])
        record["status"] = "queued"
        state.pop("failed_step", None)
        store.write(state)
        store.log(state, "ดำเนิน fit ต่อด้วย wardrobe lock ที่แก้แล้วและ staging ใหม่")
        token = record["token"]
    return run_continuation(store, token)


def publish_color_revision(store, state, avatar):
    # Only called after the normal approval, reopen and QA gates.
    import os, shutil
    plan = load(Path(state["color_revision"]))
    destination = Path(state["color_delivery_target"])
    original = Path(plan["out"]) / "original_delivery.iAvatar"
    if destination.exists() and not original.exists():
        shutil.copy2(destination, original)
        if digest(destination) != digest(original):
            raise Blocked("สำรองไฟล์สีเดิมไม่ผ่าน")
    if not destination.exists() or digest(destination) != state["export_sha"]:
        tmp = destination.with_name("."+destination.name+".color_pending")
        try:
            shutil.copy2(avatar,tmp)
            if digest(tmp) != state["export_sha"]:
                raise Blocked("สำเนาสีใหม่ไม่ตรง SHA")
            os.replace(tmp,destination)
        finally:
            tmp.unlink(missing_ok=True)
    slug=state["story"]
    manifest=store.story_manifest(slug)
    wardrobe_path=store.runs/slug/"wardrobe_design.json"
    wardrobe=load(wardrobe_path)
    actor=manifest["characters"][plan["actor"]]
    look=wardrobe["looks"][plan["actor"]]
    upper=next(x for x in look["outfit"] if x["slot"]=="upper")
    source_spec=upper.get("source_spec")
    for spec in actor["outfit"]:
        if spec[0]==source_spec or spec[0]==upper.get("resolved_source_path"):
            spec[1]=plan["fabric_id"]
            break
    else:
        raise Blocked("ไม่พบเสื้อเดิมใน manifest")
    upper.update(fabric_id=plan["fabric_id"],target_color=plan["color"],
                 visual_color_verified=True,brief_reason=plan["description"])
    actor["latest_color_project"]=plan["target"]
    save(wardrobe_path,wardrobe)
    save(store.root/"stories"/f"{slug}.json",manifest)
    store.log(state,"ส่งไฟล์สีใหม่หลัง QA สำเร็จ เก็บต้นฉบับสีเดิมไว้ในรอบแก้สี")


def color_revision_state(store, previous, plan_path, finished):
    plan = load(plan_path)
    slug = previous["story"]
    actor = store.story_manifest(slug)["characters"][plan["actor"]]
    return {"story":slug,"actor":plan["actor"].removeprefix(slug+"_"),
            "age":f'{actor["age"]} ปี',"label":"ai_cc5_color_"+uuid4().hex[:8],
            "new_actor":True,"review_tools":previous["review_tools"],"phase":"พร้อม",
            "done":[],"finished_actors":sorted(finished),"color_revision":str(plan_path),
            "build_job":plan["actor"]+"_color_revision"}


def new_actor_action(store, state, temp, key):
    import kit

    slug, short = state["story"], state["actor"]
    actor_key = f"{slug}_{short}"
    job = state.get("build_job") or actor_key
    story = store.story_manifest(slug)
    actor = story["characters"][actor_key]
    job_dir = Path(kit.JOBS) / job
    folder = store.folder(state)
    recipe = store.root / state["review_tools"]
    project = job_dir / (actor["name"] + ".ccProject")
    face = job_dir / "face.png"

    def command(script, *args, timeout=240):
        return ai_cc5.run_step_command(store, state, temp, ai_cc5.python(script, *args), timeout)

    if state.get("color_revision"):
        plan_path = Path(state["color_revision"])
        plan = load(plan_path)
        if plan["actor"] != actor_key or digest(Path(plan["source"])) != plan["source_sha"]:
            raise Blocked("ต้นฉบับแก้สีเปลี่ยนหรือคนละตัวละคร")
        project = Path(plan["target"])
        if key == "select":
            if not Path(plan["texture"]).is_file():
                raise Blocked("ไม่มี texture สีใหม่")
            return
        if key == "open":
            with lock(store.runs / ".cc5_global_production_flow.lock"):
                command(recipe / "qa_bridge.py", "cc5/probes/open_path.py", f"path={plan['source']}")
            return
        if key == "fit":
            with lock(store.runs / ".cc5_global_production_flow.lock"):
                if not project.exists():
                    command(recipe / "qa_bridge.py", "cc5/probes/recolor_existing_upper.py",
                            f"plan={plan_path}", "timeout=110", timeout=125)
            evidence = load(plan_path.parent / "color_evidence.json", {})
            if evidence.get("target") != str(project) or not evidence.get("changed") or not all(
                ai_cc5.png(plan_path.parent / (name+".png")) for name in ("front","side","back")):
                raise Blocked("หลักฐานเปลี่ยนสีไม่ครบ")
            save(folder / "look.json", {"source":plan["source"],"target":str(project),"color_revision":str(plan_path)})
            return

    if key == "select":
        from tools.cc5_culture_gate import inspect_culture
        from tools.cc5_wardrobe_lock import locked_look
        errors, _, _ = inspect_culture(story, [job])
        if errors:
            raise Blocked("; ".join(errors))
        locked_look(story, actor_key, actor)
    elif key == "open":
        command(store.root / "tools/gen_faces.py", slug, actor_key, timeout=630)
        if not ai_cc5.png(Path(kit.JOBS) / actor_key / "face.png"):
            raise RuntimeError("Tidmunz ยังไม่มีภาพใบหน้าของตัวถัดไป")
        store.log(state, "ได้ภาพใบหน้าตัวถัดไปจาก Tidmunz แล้ว")
    elif key == "fit":
        previous = Path(state["prior_project"])
        if digest(previous) != state["prior_project_sha"]:
            raise Blocked("โปรเจกต์ก่อนหน้าเปลี่ยนหลังเก็บงาน")
        if not project.exists():
            if (job_dir / "result.txt").exists():
                raise Blocked("พบงานสร้างค้างใน staging ของตัวละครนี้")
            with lock(store.runs / ".cc5_global_production_flow.lock"):
                import shutil
                face_source = Path(kit.JOBS) / actor_key / "face.png"
                if not ai_cc5.png(face_source):
                    raise Blocked("ไม่พบภาพใบหน้าตัวละครเดิมสำหรับ staging ที่แก้ชุด")
                job_dir.mkdir(parents=True, exist_ok=True)
                if face_source.resolve() != face.resolve():
                    shutil.copy2(face_source, face)
                plan_story = dict(story)
                plan_story["characters"] = {job: actor}
                manifest_path = temp / f"{job}.json"
                save(manifest_path, plan_story)
                wardrobe_path = store.root / "runs" / slug / "wardrobe_design.json"
                wardrobe = load(wardrobe_path, {})
                original_look = wardrobe.get("looks", {}).get(actor_key)
                if not original_look:
                    raise Blocked("ไม่มี wardrobe lock ของตัวละครต้นฉบับ")
                wardrobe.setdefault("looks", {})[job] = dict(original_look)
                wardrobe["looks"][job]["character_name"] = actor["name"]
                wardrobe["looks"][job]["build_retry_of"] = actor_key
                save(wardrobe_path, wardrobe)
                command(store.root / "tools/plan.py", manifest_path, job, "--no-batch")
                config = load(job_dir / "job.json")
                config["layer"] = ""
                save(job_dir / "job.json", config)
                # Replace only the just-verified, saved scene from this same continuation.
                command(recipe / "qa_bridge.py", "cc5/probes/open_path.py", f"path={previous}")
                output = command(recipe / "qa_bridge.py", "cc5/probes/clear_scene.py")
                if "avatars=0" not in output:
                    raise RuntimeError("CC5 ยังมีตัวละครค้างในฉาก")
                command(recipe / "qa_bridge.py", "cc5/build.py", f"job={job}", "defer_tidy=1", "timeout=275", timeout=310)
        result = (job_dir / "result.txt").read_text(encoding="utf-8-sig")
        store.log(state, result)
        match = re.search(r"clothes_count: (\d+)", result)
        if ("FAIL" in result or "RL_OK" not in result or not match
                or int(match[1]) != len(actor["outfit"]) or not ai_cc5.file_asset(project, ".ccProject")):
            raise RuntimeError("ผล Headshot หรือชุดของตัวถัดไปยังตรวจไม่ผ่าน")
        save(folder / "look.json", {"source": str(face), "target": str(project),
                                   "build_result": str(job_dir / "result.txt")})
    elif key == "render":
        project = ai_cc5.target_project(store, state)
        templates = Path(kit.CFG.get("cc5_animation") or
                         Path.home().parent / "Public/Documents/Reallusion/Reallusion Templates/Animation")
        walk = ("2.Human Female/Move/Walk Relaxed_2Loop.rlMotion" if actor["sex"] == "female"
                else "1.Human Male/Move/Walk_2Loop.rlMotion")
        views = folder / "views"
        with lock(store.runs / ".cc5_global_production_flow.lock"):
            if not views.exists():
                command(recipe / "qa_bridge.py", str(recipe / "qa_cast_runtime.py"),
                        f"path={project}", f"out={views}", f"motion={templates / 'Motion' / walk}",
                        f"pose={templates / 'Pose/Calibration/T-Pose.rlPose'}")
        ai_cc5.validate_render(views, project)
    elif key == "sheet":
        project = ai_cc5.target_project(store, state)
        views = folder / "views"
        ai_cc5.validate_render(views, project)
        preview = folder / "review.png"
        if not preview.exists():
            command(recipe / "make_actor_review.py", views, actor["name"], preview, timeout=45)
        state["review"] = ai_cc5.review_identity(store, state, project)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("token", nargs="?")
    parser.add_argument("--resume-import-failure", action="store_true")
    parser.add_argument("--resume-corrected-fit", action="store_true")
    args = parser.parse_args()
    store = State()
    if args.resume_import_failure:
        raise SystemExit(resume_after_import_failure(store))
    if args.resume_corrected_fit:
        raise SystemExit(resume_corrected_fit(store))
    if not args.token:
        parser.error("token is required unless --resume-import-failure is used")
    raise SystemExit(run_continuation(store, args.token))
