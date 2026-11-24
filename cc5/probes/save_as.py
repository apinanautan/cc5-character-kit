# python tools\cc5.py run cc5\probes\save_as.py path=<x.ccProject>   (save the open avatar as a new project file; nothing else touched)
import RLPy
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
av = RLPy.RScene.GetAvatars()[0]
r = RLPy.RFileIO.SaveFile(av, s, BRIDGE_ARGS["path"])  # noqa: F821
BRIDGE_RESULT = "saved error=%s" % r.IsError()
