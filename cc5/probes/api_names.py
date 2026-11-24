# python tools\cc5.py run cc5\probes\api_names.py   -> names of camera / render / selection helpers in RLPy (for picking a head close-up)
import re
import RLPy
cam = RLPy.RScene.GetCurrentCamera()
pat = re.compile(r"focus|zoom|fit|frame|pos|move|rotat|size|resolution|render|fov|distance|target|look", re.I)
out = ["camera: " + ", ".join(n for n in dir(cam) if pat.search(n) and not n.startswith("_"))]
out.append("RGlobal: " + ", ".join(n for n in dir(RLPy.RGlobal) if pat.search(n) and not n.startswith("_")))
out.append("RScene: " + ", ".join(n for n in dir(RLPy.RScene) if pat.search(n) and not n.startswith("_")))
out.append("ECameraLocationType: " + ", ".join(n for n in dir(RLPy) if n.startswith("ECameraLocationType")))
BRIDGE_RESULT = "\n".join(out)
