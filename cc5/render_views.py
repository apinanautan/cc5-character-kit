# Bridge: render the open character from front / left / back / right into <job>\view_*.png (nothing saved).
#   python tools\cc5.py run cc5\render_views.py job=<job>
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from texture_ready import wait_for_textures
d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
camera = RLPy.RScene.GetCurrentCamera()
wait_for_textures()
out = []
for tag, loc in (("front", RLPy.ECameraLocationType_Front), ("left", RLPy.ECameraLocationType_Left),
                 ("back", RLPy.ECameraLocationType_Back), ("right", RLPy.ECameraLocationType_Right)):
    RLPy.RScene.SelectObject(av)
    camera.SetCameraLocation(loc)
    p = os.path.join(d, "view_%s.png" % tag)
    RLPy.RGlobal.RenderImage(p)
    out.append(p)
BRIDGE_RESULT = "\n".join(out)
