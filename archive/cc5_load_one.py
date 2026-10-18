# Run inside CC5: open the .ccProject path written in cc5_jobs\load_one.txt
import os, RLPy
p = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "load_one.txt")
RLPy.RFileIO.LoadFile(open(p, encoding="utf-8").read().strip())
