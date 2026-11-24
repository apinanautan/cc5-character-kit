---
name: ai-cc5-garment-flow
description: Run the CC5 garment flow (image -> AI 3D top -> library skirt -> push -> wear -> physics -> weave -> tiling 25 -> hair -> final) strictly one step at a time through the Ai-cc5 Preview, so the user can see in the window which step is running and where it is stuck. Use for any request to make, fit, texture or check clothes on a CC5 character in "CC5 Characters".
---

# Ai-cc5 garment flow (20 steps, fixed order)

Project root: `C:\Users\Apinan\Documents\CC5 Characters`. Talk to the user in Thai.
The ONLY source of truth for order, commands and rules is `tools/garment_pipeline/flow_preview.py` (STEPS).
Never invent another script, skip a step, or run a later step before the earlier one is `done`.

## Preview window (the user watches this)
- Desktop shortcut: `Ai-cc5 พรีวิวขั้นตอน` (runs `pythonw tools\ai_cc5.py window`).
- The row "สร้างชุด AI 3D" shows `ขั้น N/20 · <key>`; the progress bar shows `งานชุด · ขั้น N/20`.
- Everything you do must go through the commands below so the window and its log update. Work done outside them is invisible and does not count.

## Whole character order (as the Preview window shows it)
ตรวจความพร้อม → เลือกตัว → สร้างหน้า (Tidmunz, `tools/cc5_face_queue.py`) → ส่งภาพหน้าให้ตรวจ (ntfy) →
สร้างตัว CC5 + Headshot (`tools/cc5_build_queue.py`) → เปิดงาน → **สร้างชุด AI 3D (garment steps 1–14)** → ใส่ชุด →
เตรียมตัวละครก่อนตรวจ (garment steps 15–20) → เรนเดอร์ → ภาพรวม → ส่งภาพ → รอผู้ใช้ → ส่งออก → QA → เก็บงาน.
Face/build status is read from `stories/<slug>.json` → `status[<slug>_<actor>]` (`face`, `face_delivery`, `build`);
the queues write it, so never edit it by hand to look finished.

## Loop (repeat until step 20 is done)
1. `python tools\ai_cc5.py garment status`: see which step is current. If no round is registered:
   `python tools\ai_cc5.py garment init --source <ccProject> --top-image <PNG> --age <years>`
2. `python tools\ai_cc5.py garment next`: read the current step, its command, expected files and rule. Obey the rule.
3. Run it:
   - Automatic steps: `python tools\ai_cc5.py garment run`. This runs the step's command, streams the log into the window, and records done or fail by itself.
   - Manual steps (`bottom`, `hair`, `final`) and steps that need a human eye: `garment start N`, do the work exactly as written, then go to step 4.
4. Visual steps (the run ends with "รอตรวจภาพ"):
   - Open the real PNGs and compare them against the rule's criteria.
   - Send them to ntfy (`curl.exe -s -T <png> -H "Title: <Thai>" https://ntfy.sh/Pic-Gptz`).
   - Then `garment done N --note "<what you actually saw>"` or `garment fail N --note "<reason>"`.
5. On fail: fix the cause the rule names. For example, for step 5 use a new seed in a new folder such as `top_build_s1`. Then run the same step again. Never move on past a fail.

## Order (do not change)
| # | Step | What happens |
|---|------|--------------|
| 01 | preflight | Check machine and story |
| 02 | design | Design by era, job and age |
| 03 | prep_body | CC5: save as new, remove old top, T-pose, export body |
| 04 | ref_image | Reference picture: flat front, white background, no person |
| 05 | ai_3d | Hunyuan3D → close holes → place → tightfit → push out → smooth |
| 06 | ai_shape_qc | Check the AI top's shape on the body (visual) |
| 07 | top | Smooth surface + normal map + real buttons |
| 08 | bottom | Skirt from the CC5 library (manual) |
| 09 | export_tpose | Export body + skirt in T-pose |
| 10 | align | Align to body_tpose |
| 11 | push | Push the top outside the body and skirt |
| 12 | fabric | Diffuse + button normal + physics weight map |
| 13 | qc_blender | Blender QC front/side/back (visual) |
| 14 | wear | CC5: put the top on, OBJ Y-up, Transfer Skin Weight |
| 15 | physics | Light physics: shirt hem, a little at the armpit, skirt hem |
| 16 | weave_files | Roughness = weave (white), Metallic = same picture inverted (dark) |
| 17 | weave_load | CC5: load the weave, reload the print diffuse LAST |
| 18 | tiling | Tiling 25 on Roughness + Metallic (`cc5/set_channel_tiling_ui.py`) |
| 19 | hair | Black under 50; 50+ black with grey/white roots; anything else = FIX |
| 20 | final | Save a new .ccProject → render → sheet → ntfy → QA Q01–Q10 |

Why this order: you can't build a top until the reference picture is good (4→5). The AI shape must pass before you spend time on detail (6→7). The top can only be pushed outside the skirt once the real skirt is on (8→11). Textures and QC come before wearing it in CC5 (12–13→14). Physics and the weave go on the cloth that is already worn (14→15–18). Final comes last.

## Hard rules
- Never overwrite source files. Always save .ccProject as a new file. Never save .ccCloth.
- Never delete `face_chat_context.json` or source files. Never force-close an unsaved CC5.
- Don't run heavy CC5 and Blender jobs at the same time. OBJs sent to CC5 must be Y-up.
- A file existing is not a pass. Steps 6, 13, 19 and 20 need a look at the real picture.
- If preflight says BLOCKED, stop and tell the user.
