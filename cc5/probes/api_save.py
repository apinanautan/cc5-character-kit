import RLPy
s = RLPy.RSaveFileSetting()
BRIDGE_RESULT = "RSaveFileSetting: " + ", ".join(n for n in dir(s) if not n.startswith("_")) + " | RFileIO: " + ", ".join(n for n in dir(RLPy.RFileIO) if not n.startswith("_"))
