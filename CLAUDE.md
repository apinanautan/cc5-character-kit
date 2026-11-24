# CC5 Characters — UNIVERSAL PROJECT ENTRYPOINT
This project handles hundreds of stories. Do not assume any previous or newest story is active.
Before ANY face, hair, costume, character, image or export task:
1. Verify hostname DESKTOP-F1PJT4S using Dino Tunnel.
2. Read canonical live master: docs/production/THAI_CHARACTER_MASTER.md.
3. Read docs/production/ERA_PROFILES.json, FACE_TIDMUNZ_PIPELINE.md and NTFY_REVIEW.md.
4. Read docs/CHARACTER_QA_STANDARD.md and FACE_GUIDE.md, then the requested story's script/manifest.
5. Confirm story JSON matches studio/runner.py expected schema, and plan face/Headshot via installed Tidmunz Studio FIRST.
6. Distinguish epoch/social tier, commoners vs court/royals, business vs rural, historical vs mythology. The user requires Thai faces where story is Thai; never use Western stock CC5 base faces as final.
7. Record every character's source hair/clothing/real color and silhouette in per-story Lookbook. No copied source avatar/clothing meshes merely for cataloging.
8. After each requested face/actor review image render, deliver actual PNG to https://ntfy.sh/Pic-Gptz with verified receipt and dedup.
9. QA Q01-Q10 before marking PASS. Export file exists != visually verified character.
10. Current story/status and project task notes live in PROJECT_MEMORY.md, stories/<slug>.json and runs/<slug>/; do not encode them in the UNIVERSAL rules.
11. Plugin cc5-project-sync is a portable snapshot that references this live master through Dino Tunnel. Disk changes do not mutate packaged plugin; versioned release via Plugin Creator required.
No automation, deletion, restart, forced close of unsaved CC5, background worker or backup unless user specifically authorizes it.
## Global executable gate (v1.1.0)
Before work run python tools/cc5_production_preflight.py --story STORY_SLUG --runtime; BLOCKED means stop. Runner enforces schema read-only. Read docs/production/SCHEMA_RUNNER_GATE.md and docs/production/CODE_REALITY_AND_SAFETY.md. Existing tools/plan.py copies assets to job staging and Runner can restart CC5; do not claim zero copies or risk unsaved scenes.
MANDATORY PARALLEL FLOW (2026-11-14): Run tools/cc5_face_queue.py for independent Tidmunz face generation and tools/cc5_build_queue.py for CC5/Headshot builds AT THE SAME TIME. CC5 has exactly one consumer to protect global batch.txt, but it begins on the first ready face instead of waiting for the full cast. On HTTP 429 or connection reset, the face producer defers the affected actor and continues other independent faces. Both persist progress under runs/STORY_SLUG and deliver actual review images through ntfy. NEVER delete face_chat_context.json or source files. Technical iAvatar is not visual QA PASS.
## Deterministic wardrobe policy (code enforced 2026-11-14)
- New actor stories use studio/runner.py:create_story calling tools/cc5_wardrobe_autoplan.py:recommend. Explicit era (modern rural or urban), age, role and real asset paths are required. Every item/hair is locked in runs/STORY/wardrobe_design.json with a reason and original library path.
- tools/plan.py uses tools/cc5_wardrobe_lock.py, with no random fallback. The legacy wardrobe.pick_outfit, wardrobe.pick_hair and runner.reroll APIs have been disabled. Failed AI fabrics do not silently substitute random textures.
- The UI now requires an era choice and says analyze and lock rather than randomize. Historical/royal/ceremonial looks require separately verified period-appropriate assets; the current modern-only auto selector must block rather than guess.
- The rework queue is for technical CC5 processing, not automatic visual QA approval. Inspect actual body renders and front/side/back garment textures, colors and role accuracy. Any ambiguous outfit must be marked FIX, not PASS.
- Prior exported actors remain unchanged; rebuild errors go into separate story/output folders. Do not erase source faces or their chat contexts.