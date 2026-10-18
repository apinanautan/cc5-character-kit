# Bridge: open a job's saved character (e.g. right before File > Export > iAvatar by hand).
#   python tools\cc5.py run cc5\open_job.py job=krong_urai_40
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
BRIDGE_RESULT = "%s open, avatars=%d" % (name, len(RLPy.RScene.GetAvatars()))
