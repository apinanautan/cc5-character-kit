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
