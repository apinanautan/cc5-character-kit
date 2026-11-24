# UNIVERSAL CC5 STORY SCHEMA AND PREFLIGHT — v1.1.0
Use for every story. This documentation contains no specific story/cast.

Tool: tools/cc5_production_preflight.py
Before any face generation, planning, CC5 build or export, from project root:
  python tools/cc5_production_preflight.py --story STORY_SLUG --runtime
  python tools/cc5_production_preflight.py --selftest
Exit 2 BLOCKED: fix data before execution; do not bypass by creating generic stock face.
Exit 0 READY_FOR_NEXT_GATE: structural readiness only; DOES NOT mean image generation, Headshot, visible colors or exports are verified.

REQUIRED real Runner contract (studio/runner.py + tools/gen_faces.py + tools/plan.py):
- story is a JSON object: title nonempty, out_dir nonempty absolute Windows path, status a dictionary and characters a dictionary keyed by job IDs.
- each job: name, sex male/female, nonnegative integer age, age_group (baby, child, adult, middle, old), nonempty outfit list of [source_asset, fabric_or_null] pairs.
- when generating a face: face dictionary with Thai builder keys อายุ, เพศ, บทบาท, สีผิว, ใบหน้า, optionally ref. If reusing same physical head, use a valid head_from job reference.
- choose and verify era/social-tier/role/scene separately before costume decisions. Raw character planning lists are NOT runnable schema; do not invent missing ages or costumes.
- Runner.run now imports inspect_story from tools/cc5_production_preflight.py and blocks malformed schema before changing jobs or using CC5.

Verified 2026-11-14: tool selftest passed; invalid real story blocked for characters list, status string and out_dir null. A direct Runner.run test returned 3 BLOCKED messages without modifying the story. Tidmunz runtime files exist and relay port responds, but no actual image-generation call was made in that test.