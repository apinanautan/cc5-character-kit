# python tools\cc5.py run cc5\probes\drop_prop.py name=node_0   (remove one prop from the open scene)
import RLPy
for o in RLPy.RScene.GetProps():
    if o.GetName() == BRIDGE_ARGS["name"]:  # noqa: F821
        RLPy.RScene.RemoveObject(o)
BRIDGE_RESULT = str([o.GetName() for o in RLPy.RScene.GetProps()])
