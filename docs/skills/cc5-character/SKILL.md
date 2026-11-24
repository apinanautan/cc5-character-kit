---
name: cc5-character
description: Universal CC5 actor pipeline for all stories; Thai and period-accurate facial identity via Tidmunz Studio, Headshot, wardrobe, QA and ntfy.
---

# Live project canonical skill — ALL STORIES
Read project docs/production/THAI_CHARACTER_MASTER.md, ERA_PROFILES.json, FACE_TIDMUNZ_PIPELINE.md and NTFY_REVIEW.md BEFORE any character task. These files, not a previously completed story or a static ChatGPT plugin snapshot, hold current universal policy.
Confirm Windows hostname DESKTOP-F1PJT4S through Dino Tunnel. Read relevant story and its per-story Lookbook. Validate Runner schema, era/social tier and character role.

For revisions to an existing actor, read `docs/production/CC5_EXISTING_ACTOR_REVIEW_FLOW.md`. Work on one actor and age version, use an explicit single-actor command, send the inspected preview, and wait for the user before starting the next actor.

When creating a new face: tools/gen_faces.py -> kit.image_gen() -> Tidmunz Studio snapgen_image_gen.py -> Chrome Relay -> actual face.png -> CC5 Headshot 3. Do not skip Headshot and export a generic Western-looking CC5 stock face as final. Use Thai photorealistic ID portraits (where story Thai), era- and age-correct, inspected for unique face identity, neutral front lighting and visible face. Do not invent image delivery or fallback face success.

Wardrobe: choose era + class + role + region + occasion. Modern urban and modern rural distinct; historical commoners and royalty/court distinct; mythic regalia not automatically historical. Log original asset source path, cut, shoes, jewelry and visually verified actual color. Avoid same silhouette on different characters by merely changing color.

QA: docs/CHARACTER_QA_STANDARD.md Q01-Q10 including front/side/back, facial features, textures, cloth penetrations, actual iAvatar export and reopen. Keep TECHNICAL_EXPORT separate from VISUAL_QA PASS.
After each actual image review output, send PNG to https://ntfy.sh/Pic-Gptz and verify attachment + topic + id; dedup. Keep story-specific tasks/state outside this global skill; do not copy entire source models or make unasked backups.
## Global executable gate (v1.1.0)
Before work run python tools/cc5_production_preflight.py --story STORY_SLUG --runtime; BLOCKED means stop. Runner enforces schema read-only. Read docs/production/SCHEMA_RUNNER_GATE.md and docs/production/CODE_REALITY_AND_SAFETY.md. Existing tools/plan.py copies assets to job staging and Runner can restart CC5; do not claim zero copies or risk unsaved scenes.
## New face / Headshot production
For new-face jobs, use the Tidmunz face and build flow. Follow the user’s scope and review gates. Run the face and build queues concurrently only when the user has authorized work on multiple new actors. Use one CC5 consumer. Preserve source files and face chat context.
## Deterministic wardrobe policy (code enforced 2026-11-14)
- New actor stories use studio/runner.py:create_story calling tools/cc5_wardrobe_autoplan.py:recommend. Explicit era (modern rural or urban), age, role and real asset paths are required. Every item/hair is locked in runs/STORY/wardrobe_design.json with a reason and original library path.
- tools/plan.py uses tools/cc5_wardrobe_lock.py, with no random fallback. The legacy wardrobe.pick_outfit, wardrobe.pick_hair and runner.reroll APIs have been disabled. Failed AI fabrics do not silently substitute random textures.
- The UI now requires an era choice and says analyze and lock rather than randomize. Historical/royal/ceremonial looks require separately verified period-appropriate assets; the current modern-only auto selector must block rather than guess.
- The rework queue is for technical CC5 processing, not automatic visual QA approval. Inspect actual body renders and front/side/back garment textures, colors and role accuracy. Any ambiguous outfit must be marked FIX, not PASS.
- Prior exported actors remain unchanged; rebuild errors go into separate story/output folders. Do not erase source faces or their chat contexts.
