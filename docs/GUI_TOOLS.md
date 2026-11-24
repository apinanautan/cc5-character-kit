# CC5 GUI shortcuts (no screenshot-and-click)

Ported from iClone Story Pipeline (2026-11-19). Use these instead of screenshotting and clicking step by step.
Script work inside CC5 still goes through the bridge: `python tools\cc5.py run <script.py>`.

## tools\cc5_gui.ps1
Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tools\cc5_gui.ps1 <command> [args]`

| command | what it does |
|---|---|
| `shot` | screenshot of the screen CC5 is on -> `%LOCALAPPDATA%\Tidmunz Studio\snapgen_data\cc5_jobs\gui_shot.png` |
| `front` | bring CC5 to the front and check it really is in front |
| `keys "ctrl+s"` | send a hotkey by key code (works with a Thai keyboard). Refuses if CC5 is not in front |
| `list` | list CC5 windows/popups and their buttons |
| `press "^(OK|Yes)$"` | press a button in a small CC5 popup |
| `dialog "<full path>"` | fill an open Windows file dialog (Open/Save/Import/Export) and press Open/Save |
| `save` | Ctrl+S, wait until the title loses `*` |
| `saveas "<full .ccProject>"` | Ctrl+Shift+S + fill the dialog + check the file on disk (backs up first) |
| `open "<full .ccProject>"` | Ctrl+O + fill the dialog. Refuses if the current project is unsaved |
| `job <script.py> k=v` | same as `python tools\cc5.py run` |

## tools\cc5_popup_guard.ps1
Closes known harmless popups (offline notice, sign-up nag, plugin-compat notice, FBX "Convert All").
- `-Once -DryRun`: look once and only log what it would press (safe test)
- `-Once`: close once
- no switch: keeps running = a background worker -> only when the user authorizes it (AGENTS.md)
Log: `%LOCALAPPDATA%\CC5PopupGuard\guard.log`. Never add Save / Don't Save / Delete / Overwrite rules.

## Not ported (iClone-only)
Render/mux, AccuLips, timeline, camera Switch, sound import: motion/animation work, not character building.
