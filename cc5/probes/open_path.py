# python tools\cc5.py run cc5\probes\open_path.py path=<.ccProject / .iAvatar>
import RLPy
result = RLPy.RFileIO.LoadFile(BRIDGE_ARGS["path"])
count = len(RLPy.RScene.GetAvatars())
BRIDGE_RESULT = "avatars=%d" % count
if BRIDGE_ARGS.get("verify_textures"):
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(BRIDGE_ARGS["texture_module_dir"])))
    from texture_ready import wait_for_textures

    if result.IsError() or count != 1:
        raise RuntimeError("CC5 did not open exactly one actor")
    frames = wait_for_textures(BRIDGE_ARGS.get("scratch"))
    BRIDGE_RESULT = json.dumps({
        "source": BRIDGE_ARGS["path"], "reopened": True, "texture_check_frames": frames,
    })
