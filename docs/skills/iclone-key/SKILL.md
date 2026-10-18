---
name: iclone-key
description: Key one story part in iClone 8 into a finished video (คีย์ไอโคน): plan shots from the audio, place CC5 characters in the scene, motions, half-body cameras, audio in iClone, render mp4. Use when the user sends an audio part (audio_output\N.mp3) or says คีย์ไอโคน / คีย์ท่อน N.
---
The output is a **video file with sound**, not a project. Open only the scene file in `<story>\ฉาก\` (don't open the user's saves). Save only `E:\FileSave\N.iProject` + render `E:\Video\N.mp4` (just the audio length). Don't write anything into the G: story folder. No preview/backup/extra files. Follow the order:

1. **Plan before building** (the user must see it first): get the part's text (storyboard_history.json or the user pastes it) + time each phrase from the volume dips in the wav (no silence; there's background music: RMS per 0.1 s, below 35% of median = pause). Write a table: time | narration | what the characters do | camera. **Half-body/MCU/OTS only, no full body**, 4–6 cuts. Send it to the user to approve.
2. Load characters into the scene: `ic8_key_shot.py` (job json + shot.txt). Know the scene first: `ic8_survey.py`→survey.txt and `ic8_look.py` (top render). Known scene: บ้านครอบครัววีนา, stairs ~(4280,3700) facing -Y, yard x3700-4400 y3000-3600.
3. Create > Camera > Linear Camera (one per project; save it in the project).
4. `ic8_jobs\stage.json` → run `ic8_stage.py`: mode "stills" renders stage_shotNa/b.png → combine into one sheet (PIL, 400px) and check → fix → mode "video" renders mp4 + puts the wav (ffmpeg mp3→wav) on the hidden avatar (`audio_host`) so it doesn't lip-sync.
   - actors: pos [x,y,yaw], motions [[t,path]] (each repeats until the next), moves [[t,x,y,yaw]] = walk path (Walk.iMotion walks in place, the moves keys carry it). Keep walking until the part ends so nobody stands left behind.
   - shots: [t,[cam xyz],[target xyz]] cut instantly. Distance ~1.8–2.5 m, eye height 150–160 = half body.
   - yaw 0 = face -Y, 90 = +X, 180 = +Y.
5. Motion: `G:\ไดรฟ์ของฉัน\.ไฟล์ต่างๆ (ห้ามลบ)\โมชั่น\` → MixMoves Communication 200 (Stand Idle_Response/Idle_Talk/Arms Crossed), CC MixMove Walk, Bros&Pals Greeting Gesture (wave). Don't use Daily Life Motion.

Driving iClone (computer-use):
- Thai paths: `Set-Clipboard` in PowerShell, then Ctrl+V. **Zoom to check the box text before pressing Enter**, because the user may have copied something else.
- open_application iClone before every batch (focus slips often).
- The "script not compatible" popup that shows up when opening the Script menu is a leftover: Cancel, then open Load Python again. Missing texture: OK.
- Wait for the result from the log/png with an until-loop. Don't keep taking screenshots.
- If iClone freezes (Not Responding > 3 minutes), ask before force-closing.

RLPy gotchas: **RTime = 1/6000 s ticks (not ms!)**, int only, `FromValue(int(sec*6000))`. Render with `ic8_render.py` (render.json start/end in sec → `RGlobal.RenderVideo(start, end, path)`), then mux the audio part with ffmpeg → `E:\Video\N.mp4`. Before the full render, test-render 1 s and check the duration and the shot are correct. Camera base rotation = Rx(+90°) (don't read it from Front view; it flips on a re-run). The script's SaveFile doesn't write → use File > Save Project As yourself. `RemoveAllAnimations` before re-keying.
