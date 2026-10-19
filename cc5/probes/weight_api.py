# Bridge probe: list RLPy names about skin weights / cloth.
import RLPy
out = []
for mod in [RLPy] + ([__import__("RLPy2")] if True else []):
    for n in dir(mod):
        if any(k in n.lower() for k in ("weight", "skin", "transfer")):
            out.append(mod.__name__ + "." + n)
        obj = getattr(mod, n)
        if n in ("RIClothComponent", "RIAvatar", "RICloth", "RIObject", "RIMesh", "RISkinComponent", "RIClothComponent"):
            out += ["  %s.%s" % (n, m) for m in dir(obj) if any(k in m.lower() for k in ("weight", "skin", "transfer", "bone"))]
BRIDGE_RESULT = "\n".join(out)
