"""Offline integration checks for Ai-cc5. CC5, the desktop and ntfy are mocked."""

import contextlib
import io
import json
import re
import subprocess
import sys
import time
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import ai_cc5 as app
import ai_cc5_update as update
import ai_cc5_continue as continuation
from ai_cc5_state import Blocked, FRAMES, QA_KEYS, ROOT, STEPS, State, digest, load, save

REAL_RUN = app.run_step_command
from tools.job_tidy import tidy


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="test-ai-cc5-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.store = State(self.root)
        self.run = self.root / "runs/example"
        self.run.mkdir(parents=True)
        self.source = self.root / "source.ccProject"
        self.source.write_bytes(b"source" * 1000)
        save(self.root / "stories/example.json", {"characters": {
            "example_father_main": {"age": 44, "age_group": "middle", "sex": "male"},
        }})
        save(self.run / "CAST_QA_INVENTORY.json", {"actors": {
            "example_father_main": {"age": 44, "sex": "male", "name": "พ่อ",
                                    "chosen": {"project": str(self.source)}},
        }})
        for name in app.NEEDED[:-1]:
            (self.run / name).touch()
        (self.root / update.VERSION).write_text("1.0.0", encoding="ascii")
        self.addCleanup(patch.stopall)
        patch.object(update, "check", return_value=("", True)).start()
        self.command = patch.object(app, "run_step_command", side_effect=self.simulate).start()
        self.inspect = patch.object(app, "inspect_cc5").start()
        self.diagnose = patch.object(app, "capture", side_effect=self.screen).start()

    def cli(self, *args, expected=0):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = app.main(args, self.root)
        self.assertEqual(result, expected, out.getvalue() + err.getvalue())
        return out.getvalue() + err.getvalue()

    @staticmethod
    def image(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (100, 100), "#754186").save(path)

    def simulate(self, store, state, temp, command, timeout):
        script = Path(command[3]).name
        key = store.step(state)[0]
        if script == "cc5_production_preflight.py":
            return "PREFLIGHT READY_FOR_NEXT_GATE"
        if script == "qa_bridge.py":
            return json.dumps({"source": state["source"], "reopened": True, "texture_check_frames": 3})
        if script == "make_actor_review.py":
            self.image(Path(command[-1]))
            return ""
        fitting = store.fitting(state)
        project = self.root / "fitted.ccProject"
        if key == "fit":
            self.assertIn("--fit-only", command)
            project.write_bytes(b"fit project" * 1000)
            save(fitting / "look.json", {"source": state["source"], "target": str(project)})
            return ""
        directory = fitting / "views"
        if key == "export":
            self.assertIn("--export-reviewed", command)
            project = project.with_suffix(".iAvatar")
            project.write_bytes(b"local avatar" * 1000)
            directory = fitting / "export_check"
        for frame in FRAMES:
            self.image(directory / f"{frame}.png")
        save(directory / "runtime.json", {
            "source": str(project), "source_size": project.stat().st_size,
            "motion_frames": {"walk_00": 0, "walk_40": 24, "walk_40_side": 24, "walk_74_side": 44},
            "reopened": True, "t_pose_applied": True, "motion_applied": True,
            "review_pose_discarded": True, "iavatar_reopened": key == "export",
        })
        return ""

    def screen(self, argv, timeout=20):
        if "shot" in argv:
            self.image(Path(argv[-1]))
        if "ai_cc5_ocr.ps1" in " ".join(argv):
            self.ocr_input = Path(argv[-1])
            self.assertTrue(self.ocr_input.is_file())
            return "ข้อความ OCR"
        return "ข้อความ UIA"

    def start(self, *flags):
        self.cli("use", "example", "father_main", *flags)

    def through_sheet(self):
        self.start()
        self.cli("do")
        self.cli("do")
        for _ in range(3):
            self.cli("do", "--allow-cc5")
        self.cli("do")

    def test_one_step_and_dry_run_read_only(self):
        self.cli("use", "example")
        before = self.store.state_file("example").read_bytes()
        self.assertIn("preflight", self.cli("do", "--dry"))
        self.assertEqual(before, self.store.state_file("example").read_bytes())
        self.command.assert_not_called()
        self.cli("do")
        self.cli("do", expected=2)
        self.start()
        self.cli("do")
        self.assertEqual(self.store.active()["done"], ["preflight", "select"])
        self.assertIn("do --allow-cc5", self.cli("do", expected=2))
        self.inspect.assert_not_called()
        self.assertIn("44 ปี", self.cli("status"))

    def test_failure_has_timed_log_uia_ocr_and_one_image(self):
        self.start()
        self.command.side_effect = RuntimeError("PREFLIGHT BLOCKED\nbad schema")
        self.cli("do", expected=1)
        state = self.store.active()
        self.assertEqual(state["done"], [])
        folder = self.store.folder(state)
        report = load(folder / "last_fail.json")
        self.assertEqual(report["step"], "preflight")
        self.assertIn("UIA", report["uia"])
        self.assertIn("OCR", report["ocr"])
        self.assertEqual([p.name for p in folder.glob("*.png")], ["last_fail.png"])
        self.assertFalse(self.ocr_input.exists())
        self.assertTrue(all(re.match(r"\d{4}-\d\d-\d\dT.* \+\d+\.\d+s ", line)
                            for line in (folder / "log.txt").read_text(encoding="utf-8").splitlines()))
        self.assertIn("bad schema", self.cli("log"))
        self.inspect.assert_not_called()

    def test_planning_story_opens_preparation_and_does_not_run_preview(self):
        path = self.root / "stories/example.json"
        manifest = load(path)
        manifest.update(production_stage="planning", characters={})
        save(path, manifest)
        prep = self.store.preparation_folder("example")
        prep.mkdir(parents=True)
        for name in ("01_brief.md", "02_analysis.md", "03_lookbook.md"):
            (prep / name).write_text("planning summary", encoding="utf-8")
        save(prep / "04_preflight.json", {"status": "BLOCKED", "errors": ["draft"]})
        self.cli("use", "example")
        self.assertIn("เตรียมเรื่อง 3/5 / BLOCKED", self.cli("status"))
        self.assertIn("วิเคราะห์เรื่อง", self.cli("prepare"))
        self.assertIn("Ai-cc5 prepare", self.cli("do", expected=2))
        self.command.assert_not_called()

    def test_draft_cast_target_uses_whole_brief_and_keeps_unknown_group(self):
        path = self.root / "stories/example.json"
        manifest = load(path)
        manifest["production_stage"] = "planning"
        manifest["cast_brief"] = {
            **{f"actor_{i}": {"name": f"Actor {i}"} for i in range(7)},
            "staff": {"name": "ช่างร่วมร้าน", "count": [2, 3]},
            "friends": {"name": "กลุ่มเพื่อน", "count": None},
        }
        save(path, manifest)
        self.cli("use", "example")
        self.assertEqual(self.store.actor_totals(self.store.active()), (0, 1))
        self.assertEqual(self.store.cast_target(manifest, 1), ("9–10 ตัว + 1 กลุ่ม", None, ("กลุ่มเพื่อน",)))
        output = self.cli("status")
        self.assertIn("เสร็จ 0 ตัว / ต้องทำ 9–10 ตัว + 1 กลุ่ม", output)
        self.assertNotIn("0/1 ตัว", output)

    def test_actor_count_tracks_variants_across_rounds_and_latest_story(self):
        path = self.root / "stories/example.json"
        manifest = load(path)
        second = "example_father_old"
        manifest["characters"][second] = {"age": 64, "age_group": "old", "sex": "male"}
        manifest["cast_brief"] = {"extras": {"age_brief": "2–3 คน"}}
        manifest["cast_finalized"] = True
        save(path, manifest)
        inventory_path = self.run / "CAST_QA_INVENTORY.json"
        inventory = load(inventory_path)
        inventory["actors"][second] = {"age": 64, "sex": "male", "name": "พ่อ",
                                       "chosen": {"project": str(self.source)}}
        save(inventory_path, inventory)
        self.start()
        state = self.store.active()
        state["done"] = [step[0] for step in STEPS[:-1]]
        self.store.write(state)
        self.assertEqual(self.store.actor_totals(state), (0, 2))
        app.complete(self.store, state, "tidy")
        self.assertIn("ตัวละครเสร็จ 1/2 ตัว", self.cli("status"))

        self.cli("use", "example", "father_old")
        state = self.store.active()
        state["done"] = ["preflight", "select"]
        self.store.write(state)
        self.assertEqual(self.store.actor_totals(state), (1, 2))
        save(self.root / "stories/next_story.json", {"title": "Next", "characters": {"next_story_one": {}}})
        self.cli("use", "next_story")
        self.assertEqual(self.store.active()["story"], "next_story")
        self.assertIn("ตัวละครเสร็จ 0/1 ตัว", self.cli("status"))
        self.assertEqual(load(self.store.state_file("example"))["done"], ["preflight", "select"])
        self.cli("use", "example")
        self.assertEqual(self.store.actor_totals(self.store.active()), (1, 2))

    def test_progress_counts_real_pngs(self):
        self.start()
        state = self.store.active()
        state["done"] = [row[0] for row in STEPS[:4]]
        self.store.write(state)
        views = self.store.fitting(state) / "views"
        self.image(views / "front.png")
        (views / "side.png").write_bytes(b"incomplete")
        # PNG with a corrupt IDAT CRC can raise SyntaxError during concurrent writes.
        corrupt = views / "side.png"
        self.image(corrupt)
        data = bytearray(corrupt.read_bytes())
        pos = data.index(b"IDAT")
        length = int.from_bytes(data[pos-4:pos], "big")
        data[pos+4+length] ^= 1
        corrupt.write_bytes(data)
        self.assertEqual(self.store.evidence_progress(state), (1, 10))
        self.assertIn("10% (1/10)", self.cli("status"))

    def test_preview_receipt_approval_export_and_visual_qa(self):
        self.through_sheet()

        def delivery(story, job, kind, preview, run):
            sha = digest(preview)
            save(run / "flow_ntfy_receipts.json", {"sent": {
                f"{job}/{kind}/{sha}": {"id": "confirmed", "hash": sha},
            }})
            return True, "confirmed"

        with patch("tools.cc5_production_flow.ntfy_send", side_effect=delivery) as send:
            self.cli("do")
            state = self.store.active()
            state["done"].pop()
            self.store.write(state)
            self.cli("do")
            send.assert_called_once()
        self.cli("do", "--allow-cc5", expected=2)
        self.cli("approve", "--said", "อนุมัติ", expected=2)
        with patch.object(app, "confirmed_chat", return_value={"said": "อนุมัติ"}):
            self.cli("approve", "--said", "อนุมัติ")
        self.cli("do", "--allow-cc5")
        self.cli("do", expected=2)
        state = self.store.active()
        qa_file = self.store.folder(state) / "qa.json"
        report = load(qa_file)
        for key in QA_KEYS:
            report["checks"][key] = {"result": "PASS", "evidence": f"view inspected for {key}"}
        save(qa_file, report)
        self.cli("do")
        self.assertIn("100%", self.cli("do"))

    def test_preview_button_waits_for_confirmed_current_review_and_is_one_shot(self):
        self.through_sheet()
        state = self.store.active()
        self.assertFalse(continuation.approval_ready(self.store, state))

        def delivery(story, job, kind, preview, run):
            sha = digest(preview)
            save(run / "flow_ntfy_receipts.json", {"sent": {
                f"{job}/{kind}/{sha}": {"id": "confirmed", "hash": sha},
            }})
            return True, "confirmed"

        with patch("tools.cc5_production_flow.ntfy_send", side_effect=delivery):
            self.cli("do")
        state = self.store.active()
        self.assertTrue(continuation.approval_ready(self.store, state))
        with patch.object(app, "target_project", return_value=self.source), \
             patch.object(app, "review_identity", return_value=state["review"]):
            token = continuation.approve_click(self.store, state)
            with self.assertRaises(Blocked):
                continuation.approve_click(self.store, state)
        approved = self.store.active()
        self.assertEqual(approved["approval"]["origin"], "preview_button")
        self.assertEqual(approved["continuation"], {"token": token, "status": "queued"})

    def test_preview_button_rejects_stale_round(self):
        self.through_sheet()
        shown = self.store.active()
        shown.update(delivery={"id": "old", "sha": "old"}, review={"review_sha": "old"})
        current = dict(shown, label="new-round")
        self.store.write(current)
        with self.assertRaises(Blocked):
            continuation.approve_click(self.store, shown)
        self.assertNotIn("approval", self.store.active())

    def test_button_continuation_runs_delivery_steps_then_starts_one_next_actor(self):
        self.start()
        state = self.store.active()
        state["done"] = [step[0] for step in STEPS[:8]]
        state.update(approval={"origin": "preview_button", "receipt": "receipt", "review_sha": "sha"},
                     continuation={"token": "one-shot", "status": "queued"})
        self.store.write(state)
        calls = []

        def advance(store, current, _args):
            step = store.step(current)[0]
            calls.append((current["actor"], step))
            app.complete(store, current, step)
            return 0

        second = dict(state, actor="second", label="second-round", done=[])
        second.pop("continuation", None)
        second.pop("approval", None)
        with patch.object(app, "do", side_effect=advance), \
             patch.object(continuation, "verified_qa") as qa, \
             patch.object(continuation, "next_ready_actor", return_value=second):
            self.assertEqual(continuation.run_continuation(self.store, "one-shot"), 0)
        self.assertEqual([step for actor, step in calls if actor == "father_main"],
                         ["export", "qa", "tidy"])
        self.assertEqual([step for actor, step in calls if actor == "second"],
                         ["preflight", "select", "open", "fit", "render", "sheet", "send"])
        qa.assert_called_once()
        self.assertEqual(self.store.active()["actor"], "second")
        self.assertNotIn("continuation", self.store.active())

    def test_detached_continuation_imports_project_tools_from_any_working_directory(self):
        script = ROOT / "tools" / "ai_cc5_continue.py"
        code = (
            "import sys; "
            f"sys.path.insert(0, {str(script.parent)!r}); "
            "import ai_cc5_continue; import tools.cc5_build_queue"
        )
        result = subprocess.run([sys.executable, "-B", "-c", code], cwd=self.root,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_resume_is_limited_to_clean_import_failure_before_export(self):
        self.through_sheet()
        state = self.store.active()
        state["done"].extend(["send", "approve"])
        state.update(phase="พร้อม", failed_step="export",
                     approval={"origin": "preview_button", "receipt": "receipt", "review_sha": "sha"},
                     delivery={"id": "receipt", "sha": "sha"}, review={"review_sha": "sha"},
                     continuation={"token": "resume-token", "status": "blocked"})
        self.store.write(state)
        save(self.store.folder(state) / "last_fail.json", {
            "step": "export", "error": "No module named 'tools'"})
        with patch.object(continuation, "run_continuation", return_value=0) as resume:
            self.assertEqual(continuation.resume_after_import_failure(self.store), 0)
        self.assertEqual(self.store.active()["continuation"]["status"], "queued")
        resume.assert_called_once_with(self.store, "resume-token")
        self.store.active()["continuation"]["status"] = "blocked"
        self.store.write(self.store.active())
        save(self.store.folder(state) / "last_fail.json", {
            "step": "export", "error": "unrelated failure"})
        with self.assertRaises(Blocked):
            continuation.resume_after_import_failure(self.store)

    def test_finish_instruction_approves_only_after_the_current_review_is_sent(self):
        self.through_sheet()
        state = self.store.active()
        state["done"].append("send")
        state["delivery"] = {"id": "receipt", "sha": state["review"]["review_sha"]}
        state["finish_request"] = {"said": "ทำต่อให้เสร็จ", "at": "2026-11-24T00:00:00+00:00"}
        self.store.write(state)
        with patch.object(app, "review_identity", return_value=state["review"]):
            continuation.finish_approval(self.store, state)
        self.assertEqual(state["approval"]["origin"], "user_finish_instruction")
        self.assertEqual(state["approval"]["said"], "ทำต่อให้เสร็จ")
        self.assertEqual(self.store.step(state)[0], "export")

    def test_resume_corrected_fit_can_reissue_a_one_shot_token_after_actor_switch(self):
        self.start()
        state = self.store.active()
        state.update(done=["preflight", "select", "open"], phase="พร้อม", failed_step="fit",
                     new_actor=True, build_job="retry_not_created",
                     finish_request={"said": "ทำต่อให้เสร็จ", "at": "2026-11-24T00:00:00+00:00"})
        self.store.write(state)
        save(self.store.folder(state) / "last_fail.json", {
            "step": "fit", "error": "ผล Headshot หรือชุดของตัวถัดไปยังตรวจไม่ผ่าน"})
        with (
            patch("tools.cc5_wardrobe_lock.locked_look"),
            patch.object(continuation, "run_continuation", return_value=0) as resume,
        ):
            self.assertEqual(continuation.resume_corrected_fit(self.store), 0)
        current = self.store.active()
        self.assertEqual(current["continuation"]["status"], "queued")
        resume.assert_called_once_with(self.store, current["continuation"]["token"])

    def test_ambiguous_delivery_is_never_reposted(self):
        self.through_sheet()
        with patch("tools.cc5_production_flow.ntfy_send", return_value=(False, "network timeout")) as send:
            self.cli("do", expected=1)
            self.cli("do", expected=2)
            send.assert_called_once()

    def test_interrupted_live_work_holds_until_recovered(self):
        self.start()
        self.cli("do")
        self.cli("do")
        self.command.side_effect = subprocess.TimeoutExpired(["mock"], 2)
        self.cli("do", "--allow-cc5", expected=1)
        self.cli("do", "--allow-cc5", expected=2)
        self.assertIn("ต้องตรวจ CC5", self.cli("status"))
        self.cli("use", "example", "father_main", "--label", "new", expected=2)

    def test_real_subprocess_wait_has_a_deadline(self):
        self.start()
        state = self.store.active()
        state["started"] = time.time()
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            REAL_RUN(self.store, state, self.root, [sys.executable, "-B", "-c", "import time; time.sleep(30)"], .1)
        self.assertLess(time.monotonic() - started, 5)

    def test_review_changes_block_delivery(self):
        self.through_sheet()
        folder = self.store.folder(self.store.active())
        Image.new("RGB", (100, 100), "#aaaaaa").save(folder / "review.png")
        with patch("tools.cc5_production_flow.ntfy_send") as send:
            self.cli("do", expected=2)
            send.assert_not_called()

    def test_wrong_age_key_and_multiple_donors_are_rejected(self):
        self.cli("use", "example", "father", expected=2)
        donors = self.run / "donors.json"
        save(donors, {"father_main": {}, "mother_main": {}})
        self.cli("use", "example", "father_main", "--donor-map", str(donors), expected=2)

    def test_approval_only_exact_latest_user_message_after_delivery(self):
        thread = "00000000-0000-4000-8000-000000000001"
        session = self.root / f"rollout-fixture-{thread}.jsonl"
        def entry(role, text, when="2026-11-24T05:00:10Z"):
            return json.dumps({"type": "response_item", "timestamp": when, "payload": {
                "type": "message", "role": role, "content": [{"type": "input_text", "text": text}],
            }})
        after = "2026-11-24T05:00:00Z"
        session.write_text(entry("assistant", "อนุมัติ") + "\n" +
                           entry("user", "อนุมัติ", "2026-11-24T04:59:59Z"), encoding="utf-8")
        with self.assertRaises(Blocked):
            app.confirmed_chat("อนุมัติ", after, self.root, thread)
        session.write_text(entry("user", "อนุมัติครับ"), encoding="utf-8")
        with self.assertRaises(Blocked):
            app.confirmed_chat("อนุมัติ", after, self.root, thread)
        self.assertEqual(app.confirmed_chat("อนุมัติครับ", after, self.root, thread)["said"], "อนุมัติครับ")


class UpdateAndCleanupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="test-ai-cc5-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_release_updates_program_and_preserves_protected_paths(self):
        protected = ("stories/example.json", "runs/example/state.json", "config.json")
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as package:
            for name in update.FILES:
                package.writestr(f"release/{name}", "2.0.0" if name == update.VERSION else "updated")
            for name in protected + ("../out-of-tree",):
                package.writestr(f"release/{name}", "must not be installed")
        for name in protected:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original", encoding="utf-8")
        update.install(self.root, archive.getvalue(), "v2.0.0")
        self.assertEqual(update.version(self.root), "2.0.0")
        self.assertEqual((self.root / "Ai-cc5.cmd").read_text(encoding="utf-8"), "updated")
        self.assertTrue(all((self.root / name).read_text(encoding="utf-8") == "original"
                            for name in protected))
        self.assertFalse((self.root / "out-of-tree").exists())
        with self.assertRaises(ValueError):
            update.install(self.root, archive.getvalue(), "v3.0.0")
        self.assertEqual(update.version(self.root), "2.0.0")

    def test_release_check_is_throttled_even_when_unavailable(self):
        (self.root / update.VERSION).write_text("1.0.0", encoding="ascii")
        with patch.object(update, "get", side_effect=OSError("no network")) as get:
            self.assertEqual(update.check(self.root), ("", False))
            self.assertEqual(update.check(self.root, explicit=True), ("no network", False))
            get.assert_called_once()

    def test_tidy_keeps_failed_jobs_and_only_cleans_known_copies(self):
        job_dir = self.root / "job"
        job_dir.mkdir()
        original = self.root / "library.ccCloth"
        original.write_text("material", encoding="utf-8")
        copy = job_dir / "item0.ccCloth"
        copy.write_bytes(original.read_bytes())
        (job_dir / "name.ccProject").touch()
        (job_dir / "face.png").touch()
        layers = job_dir / "layer_fix"
        layers.mkdir()
        (layers / "stage.obj").touch()
        (layers / "keep.txt").touch()
        job = {"name": "name", "items": [copy.name], "sources": {copy.name: str(original)}}
        tidy(job_dir, job, "name", ["FAIL save"])
        self.assertTrue(copy.exists())
        tidy(job_dir, job, "name", ["OK   save"])
        self.assertFalse(copy.exists())
        self.assertTrue(original.is_file())
        self.assertTrue((job_dir / "face.png").is_file())
        self.assertFalse((layers / "stage.obj").exists())
        self.assertTrue((layers / "keep.txt").exists())
        self.assertEqual(load(job_dir / "job.json")["items"], [str(original)])

    def test_source_has_no_machine_drive_paths(self):
        paths = list(update.FILES) + ["tools/test_ai_cc5.py", "tools/ai_cc5_continue.py"]
        story = ROOT / "runs/chai_chana_khon_mai_yom_phae"
        paths += [str((story / name).relative_to(ROOT)) for name in
                  ("review_cast.py", "qa_bridge.py", "qa_cast_runtime.py",
                   "qa_export_fitting.py", "make_actor_review.py")]
        for relative in paths:
            path = ROOT / relative
            if path.is_file():
                text = path.read_text(encoding="utf-8-sig")
                self.assertIsNone(re.search(r"(?i)(?<![a-z0-9_])[a-z]:[\\/]", text), relative)


if __name__ == "__main__":
    unittest.main()
