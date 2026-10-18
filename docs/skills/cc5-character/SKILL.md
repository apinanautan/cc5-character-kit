---
name: cc5-character
description: Build one Thai folk-tale (นิทานพื้นบ้าน) 3D character in Character Creator 5 from an AI face, dressed with the user's own clothes/hair library, rendered full-body and saved into the story folder. Use when the user asks to make/create a character in CC5 / Character Creator ("ทำตัวละคร", "สร้างคาแรคเตอร์", "ทำ <ชื่อ> ใน CC5").
---

# สร้างตัวละคร CC5 ทีละตัว (นิทานพื้นบ้านไทย)

Proven on 2026-10-04 (นายชัยวัยกลางคน): face → Headshot 3 → hair/shirt/pants/sandals → black hair → full-body render → saved to G:.

## Rules from the user (never break)
- Style = นิทานพื้นบ้านไทย: simple village/old-Thai clothes. No sci-fi, armor, camo, party/revealing, logos, flashy fashion.
- Hair color: **black only, or gray for old people**. Never brown/blond/dyed. The script dyes hair: `hair_rgb` [18,16,15] black, [120,118,115] gray.
- Use the user's own library, not Reallusion Templates:
  `G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น\Prop ของใช้ต่างๆ\เสื้อผ้า-ทรงผม`
  Asset types: clothes `.ccCloth/.iCloth`, shoes `.ccShoes`, gloves `.ccGloves`, hair/beard/brows `.ccHair/.rlHair/.iHair`, accessories `.ccAcc/.iAcc`. `.iAvatar` are whole characters, not parts.
- File names lie; judge each item by its embedded preview picture (first JPEG/PNG in the file with a gray studio background — see `snapgen_cc5_catalog.extract_thumbnail`). Many `.ccAcc` previews show a whole dressed character, so look carefully at what the item itself is.
- Do not change the user's program code for a one-off character.
- **File names are English only**, using the karaoke romanization of the character: `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\karaoke_romanizations.json` (e.g. นายชัยตอนวัยกลางคน → `Nai Chai Middle-aged`). Never Thai, never a placeholder. `job.json` "name" = that English name. Don't overwrite existing files of the user.
- **Put only ONE file in the story folder: the exported `.iAvatar`.** The script's check render `.png` and `.ccProject` stay in the job folder (never copy them to the story folder — the user finds it cluttered). Export: CC5 menu File → Export → iAvatar → Export settings "Export" → save dialog opens in the last folder; set file name (click box, Ctrl+A, type `<English name>.iAvatar`), Enter. There is no Python API for iAvatar export; do it through the UI after the script finishes.
- **Vary hairstyles**: never give every character the same hair (e.g. `Classic short` on everyone). Pick a different suitable black/gray hairstyle per character (randomize among fitting ones), and track which hairs the story already used.
- **Body type**: use **Neutral** for ordinary adults and old people (clothes fit it best); **Child**/**Baby** for children. Use Male/Female only when the script says the character is muscular/very masculine (big muscles or a busty female body make clothes hard to fit).
- **Make the head through the Headshot 3 "Generate Character" window** (user's preferred way; scripting `CenerateCharacter` once hung CC5): Headshot 3 panel → Regenerate Character → HEAD: folder icon, load the face → BODY tab: body type (see above), Age Adult/Elder/Teen to match → GENERATE (~1.5–3 min). **Never tick "Generate Hair"** (hair comes from the library; generating it wastes time). A "Failed to record undo/redo step" popup afterwards is harmless — click OK. Then run the script with `"skip_headshot": true` to strip/dress/dye/render/save.
- The face photo must already look the right age — Headshot copies it. Check the face before generating (old faces made by an earlier นิทาน version look ~45 even for "หนุ่ม"; regenerate a young face if so).
- Avoid `.iCloth` (iClone cloth) items for now: loading one is the suspected cause of a CC5 hang (unproven).
- Never overwrite unsaved CC5 work: before running, the CC5 window title must not end with `*`. If it does, ask the user to save.
- ChatGPT attachment (file_upload) quota is shared with the user's work — don't burn it. If it is used up, generate the face without attaching a reference (user approved this fallback).

## Steps
1. **Face**: use `Desktop\Project snapgen.ai\export\story_face\<ชื่อ>_face.png` if it exists (front, neutral, gray background). Otherwise generate one with `snapgen_modules/snapgen_image_gen.generate_image(prompt, output_dir=...story_face, name_hint="<ชื่อ>_face", aspect_ratio="1:1")` — Thai person, exact age, front ID photo, neutral, mouth closed, light-gray background, ears visible, no hair over forehead. Look at it before continuing.
2. **Pick outfit** (show the user a contact sheet if unsure): hair (+beard/brows if needed), upper, lower (or one full outfit), shoes. Catalog with names/ratings: `%LOCALAPPDATA%\Tidmunz Studio\cc5_catalog\catalog.json` (fields name_th, part, gender, age, style, folk_fit 0-3, path, thumb). Only folk_fit ≥ 2, and verify the thumbnail yourself.
3. **Job folder** (ASCII path, CC5 can't take Thai paths for Headshot): e.g. `Desktop\Project snapgen.ai\export\cc5_test\<ascii_name>\`. Copy `face.png`, the item files (rename to ascii like `hair.rlHair`, `shirt.ccCloth`), and the program script (see Cheap workflow). Write `job.json`:
   ```json
   {"face": "face.png", "body": "male", "items": ["hair.rlHair", "shirt.ccCloth", "pants.ccCloth", "shoes.ccShoes"],
    "hair_rgb": [18, 16, 15], "name": "นายชัยวัยกลางคน",
    "out_dir": "G:\\ไดรฟ์ของฉัน\\<เรื่อง>\\<โฟลเดอร์ตัวละครของเรื่อง>"}
   ```
   `out_dir` = the story folder in Google Drive where the user saves this story's characters (find recent `.iAvatar`/`.ccProject` there). `body`: male / female / neutral.
4. **Run in CC5** with computer-use (apps: "Character Creator v5.07"; clipboardWrite for typing paths): menu **Script → Load Python** (menu bar "Script" ≈ x402,y31 full-res; "Load Python" just below), type the full path of `cc5_build_character.py` in the file box, Enter. Headshot takes ~3 min.
5. **Export iAvatar** into the same `out_dir` with the English name (see rules).
6. **Verify**: wait for `result.txt` (every line must start with OK), then open `<out_dir>\<name>.png` and check: face matches, hair black/gray, whole body incl. shoes visible, clothes not clipping. Send the render to the user (SendUserFile).

## Known facts / troubleshooting
- If Headshot shows "Failed to detect facial landmarks", check `cv2` in CC5 Python: `"C:\Program Files\Reallusion\Character Creator 5\Bin64\CharacterCreatorpy.exe" -c "import cv2"`. On 2026-10-04 this was a RAM bit flip in the cached `python3.dll` (forwarder `python38`→`python3\xb8`); a PC restart fixed it. Never send the user to Reallusion Hub.
- APIs used: `RLPy2.Headshot3.GetInterface().CenerateCharacter(...)`, `avatar.GetClothes/GetHairs/GetAccessories`, `RScene.RemoveObject`, `RFileIO.LoadFile` with the avatar selected, hair shader params `RootColor`/`TipColor` + `AddDiffuseKey`, `RScene.GetCurrentCamera().SetCameraLocation(ECameraLocationType_Front)`, `RGlobal.RenderImage`, `RFileIO.SaveFile(..., ESaveFileType_Character)`.

## Cheap workflow (since 2026-10-04 — follow this, saves tokens)
- Script lives in the program: `%LOCALAPPDATA%\Tidmunz Studio\snapgen_modules\cc5\cc5_build_character.py` (repo `snapgen_modules/cc5/`). Never write scripts/jobs under `export\`.
- Jobs: `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\<ascii_name>\` (face.png, item files, job.json). Point the script at it by writing the folder path to `cc5_jobs\current_job.txt`. Re-running the script re-dresses the avatar (use it to swap hair/clothes).
- **Wardrobe data**: `snapgen_data\cc5_wardrobe.json` — items already tried (path, part, name, status ok/broken/rejected, used_by). Pick from status ok first; never use broken/rejected; add every newly tried item. Choose new items by file name (e.g. hair names are descriptive) instead of opening thumbnails.
- `.ccHair` files do NOT load in CC5 (LoadFile returns in 0.0s, nothing appears). Use `.rlHair` only.
- UI clicks (maximized CC5, 1456x819 frame): Script menu (400,30) → Load Python (442,53); file dialog takes ~10s; filename box (600,711), dialog opens in the cc5 folder so type `cc5_build_character.py`. File (13,30) → Export (62,200) → iAvatar (318,206) → Export (654,576) → name box (600,663).
- Don't screenshot while waiting; read `result.txt` with Bash instead. One small screenshot (scale 0.3) only when a step fails. Read the render png once at the end.
- **Hair = random pick, never by hand**: `python <program>\snapgen_modules\cc5\cc5_pick_hair.py <job_dir> <male|female> <child|adult|middle|old>`. Pool `snapgen_data\cc5_hair_pool.json` (checked by eye 2026-10-04; male pool has no long/mullet/topknot styles). It skips hairs used by other jobs and sets hair_rgb: black child/adult, gray middle, white old. Add new hairs to the pool only after looking at their preview.
