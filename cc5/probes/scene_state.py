import RLPy
av = RLPy.RScene.GetAvatars()[0]
BRIDGE_RESULT = "clothes=%s props=%s acc=%s" % ([c.GetName() for c in av.GetClothes()], [p.GetName() for p in RLPy.RScene.GetProps()], [a.GetName() for a in av.GetAccessories()])
