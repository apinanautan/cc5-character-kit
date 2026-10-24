# Bridge: render the open character from front / left / back / right into <job>\view_*.png (nothing saved).
#   python tools\cc5.py run cc5\render_views.py job=<job>
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
d = os.path.join(kit.JOBS, BRIDGE_ARGS["job"])  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
out = []
for tag, loc in (("front", RLPy.ECameraLocationType_Front), ("left", RLPy.ECameraLocationType_Left),
                 ("back", RLPy.ECameraLocationType_Back), ("right", RLPy.ECameraLocationType_Right)):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(loc)
    p = os.path.join(d, "view_%s.png" % tag)
    RLPy.RGlobal.RenderImage(p)
    out.append(p)
BRIDGE_RESULT = "\n".join(out)
