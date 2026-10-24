import RLPy
out = []
for f in BRIDGE_ARGS["obj"].split(";"):  # noqa: F821
    RLPy.RScene.ClearSelectObjects()
    r = RLPy.RFileIO.LoadFile(f)
    out.append("%s -> %s" % (f[-40:], "error" if r.IsError() else "ok"))
out.append("props: %s" % [p.GetName() for p in RLPy.RScene.GetProps()])
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
BRIDGE_RESULT = "\n".join(out)
