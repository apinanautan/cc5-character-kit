# Bridge test: reports what CC5 has open. python tools\cc5.py run cc5\ping.py
import RLPy
avs = RLPy.RScene.GetAvatars()
BRIDGE_RESULT = "CC5 OK; avatars=%d %s" % (len(avs), [a.GetName() for a in avs])
