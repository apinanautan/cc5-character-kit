# CC5 step log (Pin, 2026-10-04) — raw notes for a one-click script

| # | step | how | time | manual? | merge idea |
|---|---|---|---|---|---|
| 1 | list missing characters | compare story_face_batch text vs *.iAvatar in story folder | 5s | no | script |
| 2 | pick outfit | cc5_find.py + 1 contact sheet of 4 thumbs | ~1 min | choose | script makes sheet, user/GPT picks number |
| 3 | build job folder | copy face, outfit, shoes; write job.json | 2s | no | script |
| 4 | pick hair | cc5_pick_hair.py — BUG: same file in 2 folders = dup not caught (compare by filename) | 2s | no | fix in picker |
| 5 | kill stuck CC5 | taskkill CharacterCreator.exe | 1s | no | script |
| 6 | start CC5 | ~70s splash, then "Failed to establish connection" popup -> OK | 70s | click | auto-dismiss in script? |
| 7 | restore prompt | "Unsaved project data found" after kill -> Cancel | 1s | click | script |
| 8 | headshot + dress in ONE run | skip_headshot=false: build script calls Headshot API itself -> no manual Headshot/BODY/GENERATE clicks (saves ~6 clicks + screenshots) | ~5 min | no | use always |
| 9 | load script | Script > Load Python > type path > Enter | 10s | 4 clicks | CC5 can autorun a startup script? check |
| 10 | check render | outfit preview showed blouse+skirt but file was blouse only -> naked legs | - | look | catalog "full" can lie: verify lower body exists; script could check wearing list for a lower piece |
| 11 | re-dress only | skip_headshot=true, add skirt, rerun script (~40s) | 40s | 4 clicks | |
| 12 | skirt + blouse together | both are "full" slot in CC5 -> the later one replaces the earlier | - | - | DATA: record real slot (upper/lower/full) per file |
| 13 | catalog labels wrong | Shirts(9)="ผ้าซิ่น" is a mermaid tail; Pants(24)/กางเกงขายาว labels don't match what loads | - | - | DATA: re-check each file by loading, not by preview picture |
| 14 | hair dup check | same rlHair in 2 folders -> picker compares full path, misses it | - | - | compare by file name |
| 15 | body | MUST be neutral for adults (user rule) — I used female by mistake | - | - | force in script |
