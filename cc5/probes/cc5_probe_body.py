# Run inside CC5: list Headshot body-type enum + current avatar height -> cc5_jobs\body_probe.txt
import os
import RLPy, RLPy2
out = ["EHSBodyType: " + ", ".join(n for n in dir(RLPy2.EHSBodyType) if not n.startswith("_"))]
for n in dir(RLPy2):
    if "Body" in n or "Age" in n:
        out.append("RLPy2." + n)
try:
    out.append("Headshot3 iface: " + ", ".join(n for n in dir(RLPy2.Headshot3.GetInterface()) if not n.startswith("_")))
except Exception as e:
    out.append("iface err %r" % e)
open(os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "body_probe.txt"), "w", encoding="utf-8").write("\n".join(out))
