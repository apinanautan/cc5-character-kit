import RLPy, os
p = BRIDGE_ARGS["path"]  # noqa: F821
RLPy.RFileIO.LoadFile(p)
av = RLPy.RScene.GetAvatars()
names = [c.GetName() for c in av[-1].GetClothes()] if av else []
RLPy.RScene.SelectObject(av[-1])
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(os.environ["TEMP"], "school_uniform_found.png"))
BRIDGE_RESULT = "avatars=%d clothes=%s" % (len(av), names)
