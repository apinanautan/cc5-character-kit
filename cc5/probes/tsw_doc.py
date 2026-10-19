import RLPy
f = RLPy.RICloth.TransferSkinWeight
out = [str(f.__doc__)]
out += [n for n in dir(RLPy) if "SkinWeight" in n or "ETransfer" in n or "EClothSkin" in n or n.startswith("ESkin")]
BRIDGE_RESULT = "\n".join(out)
