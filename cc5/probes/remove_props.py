import RLPy
names = BRIDGE_ARGS["names"].split(",")  # noqa: F821
gone = []
for p in list(RLPy.RScene.GetProps()):
    if p.GetName() in names:
        RLPy.RScene.RemoveObject(p); gone.append(p.GetName())
BRIDGE_RESULT = "removed %s; left %s" % (gone, [p.GetName() for p in RLPy.RScene.GetProps()])
