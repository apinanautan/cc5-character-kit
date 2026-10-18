# CC5 > Script > Load Python: select the top garment of the current job (first line of batch.txt), e.g. to open
# Modify > Conform by hand. The name comes from <job>\upper.txt (written by build.py).
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

want = open(os.path.join(kit.current_job(), "upper.txt"), encoding="utf-8").read().splitlines()
av = RLPy.RScene.GetAvatars()[0]
for cl in av.GetClothes():
    if cl.GetName() in want:
        RLPy.RScene.SelectObject(cl)
        break
