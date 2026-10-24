import RLPy
av = RLPy.RScene.GetAvatars()[0]
c = [c for c in av.GetClothes() if c.GetName() == BRIDGE_ARGS["name"]][0]  # noqa: F821
RLPy.RScene.SelectObject(c)
BRIDGE_RESULT = "selected " + c.GetName()
