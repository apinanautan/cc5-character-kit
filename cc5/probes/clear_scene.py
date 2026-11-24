# python tools\cc5.py run cc5\probes\clear_scene.py   (remove every avatar and prop from the open scene; nothing is saved)
import RLPy
for av in list(RLPy.RScene.GetAvatars()):
    RLPy.RScene.RemoveObject(av)
for p in list(RLPy.RScene.GetProps()):
    if p.GetName() != "Shadow Catcher":
        RLPy.RScene.RemoveObject(p)
BRIDGE_RESULT = "avatars=%d props=%s" % (len(RLPy.RScene.GetAvatars()), [p.GetName() for p in RLPy.RScene.GetProps()])
