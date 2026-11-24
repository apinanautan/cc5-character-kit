# CC5 CENTRAL PRODUCTION STANDARD — ALL STORIES
Version 1.1.0 (2026-11-14). This is universal production policy for hundreds of different stories. NO story-specific task state belongs in this file.

Canonical live source: C:\Users\Apinan\Documents\CC5 Characters\docs\production\THAI_CHARACTER_MASTER.md
Profiles: docs/production/ERA_PROFILES.json
Face procedure: docs/production/FACE_TIDMUNZ_PIPELINE.md
Review delivery: docs/production/NTFY_REVIEW.md
Technical and visual QA: docs/CHARACTER_QA_STANDARD.md
Existing-actor wardrobe review: [CC5_EXISTING_ACTOR_REVIEW_FLOW.md](CC5_EXISTING_ACTOR_REVIEW_FLOW.md)
For revisions to an existing actor, follow this workflow one actor and age version at a time. Send the inspected preview and wait for the user before starting the next actor. Use an explicit single-actor command.

## Source of truth and plugin synchronization
- The latest user's instructions and actual story facts outrank stored defaults. Story/cast status is in stories/<slug>.json and runs/<slug>/; project status is in PROJECT_MEMORY.md; do not mix them into universal rules.
- Before each job, use connected Dino Tunnel to verify Windows hostname DESKTOP-F1PJT4S, read this master, era profiles and relevant story. Do not use PS_Bot (different Windows PC).
- CC5 Project Sync plugin is a portable snapshot and reads these live docs on each task when connected; editing disk files does NOT automatically rewrite the packaged plugin. Release updates through Plugin Creator after policy changes.
- Do not delete or copy original 3D assets just for indexing. Keep original full G: paths, metadata and compact thumbnails. No redundant backups or hidden story history.

## Required interpretation
- Identify period, social rank, age, relation, region when specified, occupation, season, occasion and scene. Era and rank are independent axes.
- Examples: contemporary Thai village; contemporary Bangkok business; Ayutthaya commoner; Ayutthaya royal/court; Sukhothai commoner/court; early Rattanakosin commoner/court; mythical Thai royal/fantasy; unspecified ancient Thai requiring period clarification.
- Ordinary ancient villagers DO NOT receive royal crowns and jewelry; a king/queen/court official must have role/rank-appropriate clothing. Mythology is not automatically historical documentation.
- Characters should look plausibly Thai when the story specifies Thai identity, with distinct authentic individual facial variation, grounded ages and skin tones. No default Caucasian-looking CC5 face as a completed Thai character; no stereotyped or caricatured features.

## Mandatory face generation through installed Tidmunz Studio
1. Validate story schema before CC5 Runner: characters must be an ID-keyed object/dict, status an object/dict, out_dir a nonnull path. Each job must define compatible age, sex, outfit and face fields. Invalid story is BLOCKED, not worked around using quick exports.
2. Use the EXISTING pipeline: tools/gen_faces.py -> kit.image_gen() -> Tidmunz Studio snapgen_image_gen.py -> Chrome Relay -> real face.png -> CC5 Headshot 3 through cc5/build.py or approved CC5 skill script.
3. Check Tidmunz running and snapgen_data/chrome_relay.json configured, without revealing token. Listening port alone is not proof a face image can be produced.
4. Face photo: realistic Thai person as appropriate for script, neutral front-facing ID portrait, head/shoulders, mouth closed, both ears and forehead visible, even white studio light, plain gray backdrop, age-accurate texture and unique identity; no Western-stock-face fallback or beauty glam filter.
5. Visually QA face.png, then Headshot 3 face against source. Preserve family resemblance and age continuity, but not identical faces for unrelated characters. Missing or failed face generation blocks character completion, no silent replacement by Neutral_F/CC3+ Katherine/Caleb.
6. Read FACE_TIDMUNZ_PIPELINE.md before every face creation. If execution fails, record exact layer (story schema, Chrome relay, Tidmunz generator, face image, Headshot) and fix that layer.

## Wardrobe and era
- Select each garment and jewelry item with era + social status + region + role + occasion. Modern urban businesswear can be right for business roles, but must not be assigned indiscriminately to rural family scenes. Do not Westernize the entire cast.
- Ancient commoners wear period-grounded modest common attire; royal ceremonial garments, crowns, formal gold ornaments, mythic headdresses and special armor require explicit rank/plot evidence. Separate historical and Thai fantasy designs.
- Record original source path, hair cut/style, visible color, shirt/pants/full garment cut, material, shoes and jewelry in per-story Lookbook. Changing only HEX does not make same garment mesh a different cut.
- RLPy AddDiffuseKey success is NOT visual color verification: actual diffuse textures/shaders may override. Inspect front, side, back and close-up render before confirming selected color.
- If no asset fits, report gap and ask to model/import a suitable asset; never substitute a random Western office outfit or royal regalia to fill a slot.

## Quality gate (never skip)
- Run approved face and wardrobe planning; build in CC5 one character at a time; verify Headshot identity and fit.
- QA Q01-Q10 from docs/CHARACTER_QA_STANDARD.md: role/age/body, face, clothing, anatomy, garment penetration, UV textures, mesh/poly, actual iAvatar export and reopen test.
- Track TECHNICAL_EXPORT separately from VISUAL_QA. Only PASS after required QA, never treat nonzero iAvatar, front PNG or Lookbook status=verified as visual approval.
- Send actual face and actor render PNGs to https://ntfy.sh/Pic-Gptz for user review after each successful review-ready render; confirm HTTP topic, ID and image attachment; dedup by image/character/variant. See NTFY_REVIEW.md.
- Do not call background image work finished or create actors when CC5 is busy with unsaved user work. Never restart Windows or close a CC5/iClone/Blender unsaved scene without explicit permission.
## Global hard-gate update v1.1.0 — 2026-11-14
- Run python tools/cc5_production_preflight.py --story STORY_SLUG --runtime before any face, CC5 build or export. Nonzero BLOCKED prohibits the job, and studio/runner.py now enforces the structural gate itself.
- Read docs/production/SCHEMA_RUNNER_GATE.md for the actual Runner JSON data contract, executable commands and validated tests.
- Read docs/production/CODE_REALITY_AND_SAFETY.md for legacy plan.py asset staging copies, Runner auto-restart risk, Lookbook limitations and QA separation.
- An installed Tidmunz face-generation function or open relay port does NOT prove a new portrait can be generated; require actual face.png plus Headshot QA. Technical iAvatar != visual PASS.
- New project-wide policy must be explicitly published to the existing cc5-project-sync plugin as a new version, preserving its App binding and prompts. Per-story status remains outside universal skills.
## New face / Headshot production
For new-face jobs, use the Tidmunz face and build flow. Follow the user’s scope and review gates. Run the face and build queues concurrently only when the user has authorized work on multiple new actors. Use one CC5 consumer. Preserve source files and face chat context.
## Deterministic wardrobe policy (code enforced 2026-11-14)
- New actor stories use studio/runner.py:create_story calling tools/cc5_wardrobe_autoplan.py:recommend. Explicit era (modern rural or urban), age, role and real asset paths are required. Every item/hair is locked in runs/STORY/wardrobe_design.json with a reason and original library path.
- tools/plan.py uses tools/cc5_wardrobe_lock.py, with no random fallback. The legacy wardrobe.pick_outfit, wardrobe.pick_hair and runner.reroll APIs have been disabled. Failed AI fabrics do not silently substitute random textures.
- The UI now requires an era choice and says analyze and lock rather than randomize. Historical/royal/ceremonial looks require separately verified period-appropriate assets; the current modern-only auto selector must block rather than guess.
- The rework queue is for technical CC5 processing, not automatic visual QA approval. Inspect actual body renders and front/side/back garment textures, colors and role accuracy. Any ambiguous outfit must be marked FIX, not PASS.
- Prior exported actors remain unchanged; rebuild errors go into separate story/output folders. Do not erase source faces or their chat contexts.
## Confirmed runtime safeguards 2026-11-14
- CC5 build.py records the last loaded cloth as the upper garment. tools/plan.py must call build_load_order to load LOWER then UPPER then SHOES so layer_fix.py does not select trouser mesh as the shirt.
- External paths inside hair binary metadata are not always actual missing textures; block only a known failed hair file validated by a CC5 runtime error, recorded in data/cc5_hair_runtime_failures.json and marked bad in data/cc5_hair_pool.json. Do not blacklist every old drive-string substring.
- For costume QA, verify actual rendered colors after fabric texture application, not requested HEX alone. Check side/back for cloth penetration, hairstyles for external missing textures, and original actor brief for status/era appropriateness.
- Full technical iAvatar export/reopen is separate from visual QA PASS; mark wrong wardrobe/color/mesh FIX and rebuild in a separate source-preserving story with a locked manifest.
MANDATORY HAIR ART DIRECTION FOR FUTURE STORIES: read docs/production/HAIR_ART_DIRECTION.md and data/hair_catalog_external_g.json; inspect actual thumbnail/crop via gallery or tools/search_hair_catalog.py. GPT designs the hairstyle before searching. No random picker and no rigid cross-story no-reuse rule. External catalog items remain unapproved until rights, file format, CC5 load, and multi-angle visual QA.
