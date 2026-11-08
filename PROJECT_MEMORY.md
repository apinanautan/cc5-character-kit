# PROJECT_MEMORY.md — CC5 Characters
Updated: 2026-11-08 Asia/Bangkok

## Mandatory first-read / last-write protocol
Read this one file first before every new story, character batch, or resuming work. Do not recursively scan the project by default. After each confirmed change (new story, rule, code, wardrobe selection, build, export, error, fix, move), append a dated note with affected story, path, verified result, pending next step. If this file is stale or insufficient, read only the relevant original files or Git diff and update this record. This is an index, not a substitute for verifying actual exports. Never report work done merely because a script started. Keep unrelated running jobs undisturbed.
When working with Git, stage only related files, make a descriptive commit, and never force push or overwrite others' changes.

## Project map
Root: C:\Users\Apinan\Documents\CC5 Characters
Git remote (verified .git/config): https://github.com/apinanautan/cc5-character-kit.git, branch main. Git push not yet confirmed.
Detailed source rules: AGENTS.md; CLAUDE.md; docs/GARMENT_PIPELINE.md; docs/APP.md.
Local Skill: docs/skills/cc5-character/SKILL.md.
Wardrobe: data/wardrobe_db.json; docs/WARDROBE.md is generated and should not be hand-edited.
Stories: stories/*.json; active cast plan runs/duang_mia_noi/CAST_PLAN.md.
Use current story JSON content to confirm title; latest observed file stories/story_1108_1311.json may have been edited.

## Wardrobe — verified user requirements, 2026-11-08
Avoid the same clothing silhouette on most characters, even when recolored or retextured. Select varied tops, bottoms, shoes by era, role, age, occupation, class and character. Uniforms for students/police and robes for monks must be correct; no scrubs or casual clothing substituted. Track previously used silhouettes and inspect actual CC5 render. New asset or review required where catalog lacks a suitable item. Clothing-policy request is confirmed, but code fix is NOT confirmed. Do not run heavy Blender and CC5 concurrently.

## Story: ดวงเมียน้อย
Modern Thai rural family drama. Cast includes สุนีย์, ปรีชา, นาวี, นิวัตน์, วินัย, ปรียา, พีภพ, อรทัย, พระวัดป่า and extras, some with age or outfit variants. Motorcycle is a prop, not a CC5 character. Previous conversation mentioned exports, but this task has not reverified current complete count; do not assert it.
Export: first find confirmed matching story root in G:\ไดรฟ์ของฉัน, then use child folder <title> ตัวละคร, without making duplicate story roots. If not found, Desktop only. A folder timestamp alone is not proof of nonexistence.
Status Word document policy: black text=pending, red text=verified .iAvatar export, not mere 3D build.

## Activity log
- 2026-11-08 — Confirmed .git/config has remote origin and main branch; Git exists at C:\Program Files\Git\cmd\git.exe. No PROJECT_MEMORY.md existed previously.
- 2026-11-08 — Created single-file project activity index and configured agent/Skill first-read workflow. Actual Git publication status should be appended after verification.

- 2026-11-08: Hair made in Blender with ANA HairCraft Cards: docs/HAIR_GUIDE.md + blender/hair_center_part.py (long straight centre part, tucked behind ears). Temple gap above the ear still open. ANA is buggy on Blender 5.2: set inputs via mod.properties.inputs.Input_x.value.
- 2026-11-08 evening: Read-only/lightweight Blender 5.2.3 add-on registration test completed: ANA HairCraft Studio 1.0.2, HairCard Studio 1.0.0 and StableGen 0.5.0 all registered without fatal errors. ANA Cards asset present; HairCard operator present. Some extension cv2/PIL file-lock cleanup warnings; StableGen-ComfyUI execution and actual hair-card texture render NOT yet verified. Experiment only: docs/haircraft_test/hair_center_part_temple_v2.py adds swept-back temple guides to cover the gap above ears; Python syntax validated, NOT rendered, NOT user approved, original blender/hair_center_part.py unchanged. CC5 currently has unsaved Pin.ccProject* and Blender currently Unsaved; DO NOT close/discard CC5 or overwrite Blender; request user permission to save and temporarily close CC5 before heavy renders.
- 2026-11-08 evening: User requested hair output now. Used agent-desktop to save unsaved CC5 Pin.ccProject (title lost *) and gracefully close the CC5 application; no forced kill. Generated actual ANA HairCraft Card hair V2 (5,360 guide strands) from docs/haircraft_test/hair_center_part_temple_v2.py and pin_body.obj. Saved independently at docs/haircraft_test/trial_20261108/pin_hair_temple_v2.blend; rendered final_front.png, final_right.png, final_back.png with improved lighting. All three PNGs verified exist, Blender render completed. The user's reference requires black center-part hair with ears visible, no side/shoulder drape. Visual QA: temple area still has a hard/somewhat stepped edge on side, rear has visible part/lighter scalp artifact; needs further smoothing before CC5 import and user approval. Original blender/hair_center_part.py and docs/haircraft_test/pin_hair_test.blend preserved. Generated preview images sent inline via remote read_image in ChatGPT.
- 2026-11-08 19:14: Via Dino Tailscale, verified hair experiment V5 generated and rendered (docs/haircraft_test/trial_20261108/pin_hair_hybrid_v5.blend and v5_front/right/back.png). Visual QA of v5_right shows failed geometry: hanging detached straight rear strip, missing/scarred temple coverage and angular front hairline. V5 REJECTED, NOT suitable for CC5 import, NOT delivered as final hair. This entire ANA-cards-only procedural approach is not presently producing usable geometry. Do not claim completion; switch to a tested hair-mesh construction/curated hair-base workflow and do not interrupt currently open CC5 without saving. This new test is NOT final.

- 2026-11-08 19:30 ดวงเมียน้อย: export-only resume launched for seven essential CC5 characters; preserve original scenes, no rebuilding. Backup C:\Users\Apinan\Documents\CC5 Characters\stories\story_1108_1311.json.before_resume_20261108_193028.bak

- 2026-11-08 19:37 ดวงเมียน้อย: verified นาวีวัย18 exported to C:\Users\Apinan\Desktop\ดวงเมียน้อย\2\นาวีวัย18.iAvatar

- 2026-11-08 19:41 ดวงเมียน้อย: verified นาวีชุดนักศึกษา exported to C:\Users\Apinan\Desktop\ดวงเมียน้อย\2\นาวีชุดนักศึกษา.iAvatar

- 2026-11-08 19:42 ดวงเมียน้อย: verified วินัยวัยมัธยม exported to C:\Users\Apinan\Desktop\ดวงเมียน้อย\7\วินัยวัยมัธยม.iAvatar

- 2026-11-08 19:44 ดวงเมียน้อย: verified นิวัตน์วัยป5 exported to C:\Users\Apinan\Desktop\ดวงเมียน้อย\3\นิวัตน์วัยป5.iAvatar

- 2026-11-08 19:45 ดวงเมียน้อย: verified นิวัตน์วัยป2 exported to C:\Users\Apinan\Desktop\ดวงเมียน้อย\3\นิวัตน์วัยป2.iAvatar

- 2026-11-08 19:45 ดวงเมียน้อย: finished guarded CC5 export attempt: นาวีชุดนักศึกษา, วินัยวัยมัธยม, นาวีวัยมัธยม, นิวัตน์วัยป5, นาวีวัยประถม, นิวัตน์วัยป2; remaining: none

- 2026-11-08 19:55: ดวงเมียน้อย verified 25/25 iAvatar exports by checking Desktop files. Missing optional background roles: . Word tracker: runs/duang_mia_noi/CHARACTER_STATUS.docx (generator generate_character_status.py). Export status reconciled, not a wardrobe/visual QA signoff.

## ส่งพรีวิวให้เห็นใน ChatGPT โดยตรง (ยืนยัน 2026-11-08)
- ผู้ใช้เคยเปิดดูรูปในแชต GPT ได้ ต้องการใช้วิธีนี้เวลาอยู่บนมือถือและไม่อยากดาวน์โหลดลงเครื่องหรืออัปโหลด Google Drive ของบริษัท
- เตรียม PNG/JPG จากเรนเดอร์จริงบนเครื่อง Windows และรวมหลายตัวเป็น contact sheet ได้ (ภาพหลักล่าสุด: docs/duang_main_cast_10_20261108.jpg)
- วิธีส่งใน ChatGPT: ใช้ Remote Desktop Commander read_file กับพาธรูปบนคอม แล้วส่งต่อ content_items ที่ type=image เป็น image output ในแชตผ่าน functions.exec image() ไม่ใช่พิมพ์พาธ Windows หรือสร้าง sandbox URL ปลอม
- ภาพลักษณะนี้แสดงในบทสนทนา ChatGPT ที่รองรับ ไม่ใช่ลิงก์สาธารณะหรือไฟล์ที่แอปอื่นเปิดได้อัตโนมัติ; หากแอปไม่แสดงให้แจ้งข้อจำกัด
- ห้ามเผยแพร่ภาพส่วนตัวขึ้น GitHub public, Google Drive หรือเว็บภายนอกเพียงเพื่อพรีวิวใน GPT เว้นแต่ผู้ใช้อนุญาตชัดเจน
- ภาพตัวละครหลักที่ส่งเป็นพรีวิวตรวจ ไม่ได้ถือว่าผ่าน QA เสื้อผ้าและทรงผมแล้ว