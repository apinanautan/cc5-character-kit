# HAIR ART DIRECTION — Universal workflow for CC5 stories (2026-11-14)

Purpose: GPT acts as a character art director. It designs the hairstyle FIRST from story era, age, role, status, face shape, and cast differentiation. After that it consults actual catalog thumbnails. Never randomly pick from hair asset names. Reuse across stories is allowed when appropriate; no hard anti-duplication rule.

Shared resources for all stories:
- Central JSON: data/hair_catalog_external_g.json
- Search CLI: python tools/search_hair_catalog.py --shape "บ๊อบ" --limit 15
- Text search: python tools/search_hair_catalog.py "side part" --json
- Gallery: runs/hair_catalog_g_20261114/gallery.html
- Source image thumbnails: runs/hair_catalog_g_20261114/thumbs
- Close-up crops: runs/hair_catalog_g_20261114/crops
- Overview contact sheets: runs/hair_catalog_g_20261114/sheets
- No source model file is copied from G: to build this catalog.

Catalog contains 368 hair asset files (161 rlHair, 197 ccHair, 10 iHair), NOT 368 verified unique silhouettes. 354 files have a real Windows Shell preview and a crop. 14 items require a licensing review and lack preview. Many filenames are opaque and their visual shape is NOT verified. Image enlargement from native 125x125 or 512x512 does not create genuine extra detail.

Process for each new story:
1. Read actual story script, age, character role, social background and era. Compare all primary cast characters BEFORE assigning hair.
2. Draft explicit art direction for each: hair silhouette, parting, length, fringe, texture/color/graying, cultural/period appropriateness, uniqueness and continuity across ages.
3. Run catalog search using art-direction requirements and inspect images of 2–4 plausible candidates (full image and crop). Do not select based solely on keyword ranking or file names.
4. Allow reused assets when justified. Use prior stories only as a creative diversity signal. Avoid visually repetitive leading cast unless story specifically requires it.
5. Reject hair visually incongruous with the era, outdated unconvincing hair clumps, bizarre geometry, old low-quality textures, accessories mistaken for hair, and known broken assets in data/cc5_hair_runtime_failures.json.
6. Confirm file path and usage rights; flagged cracked/CRKD packs must not automatically be used.
7. Current CC5 wardrobe lock supports only rlHair; ccHair/iHair may need a separately verified import/conversion path. Do NOT claim these are immediately compatible or auto-selectable.
8. Only load shortlisted finalists into CC5, never all 368 one by one. Verify real 3D appearance front/side/back/top, texture paths, transparency and collisions.
9. Before locking the actual actor, record per-character Hair Design Brief, selected G asset ID/path, preview/crop, alternatives, reason, license status, epoch and final CC5/visual QA status.
10. If no suitable verified option exists, explicitly return NO_VERIFIED_MATCH and propose a custom hairstyle based on a reference. No silent substitution.

Quality statuses:
- CATALOGED: file/path and Shell thumbnail indexed; no claims about CC5.
- VISUAL_SHORTLIST: image manually inspected for the required character/era.
- LOAD_TESTED: selected hair opened successfully on an appropriate actor and needed textures present.
- VISUAL_QA_PASS: appearance verified in CC5 in multiple views against design and story brief.
Only VISUAL_QA_PASS is approved for final delivery. Technical iAvatar export alone does not suffice.

Never delete source hair, original models, prior face conversations, or other story assets. Do not run concurrent CC5 workers. The gallery and search CLI are read-only and don't modify any story or CC5 session.
