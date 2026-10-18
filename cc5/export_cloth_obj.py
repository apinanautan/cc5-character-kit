# CC5 > Script > Load Python: export the garment named in cc5_jobs\select_cloth.txt (current avatar) as OBJ
# -> cc5_jobs\cloth_check.obj  (to count real faces outside CC5)
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

want = open(os.path.join(kit.JOBS, "select_cloth.txt"), encoding="utf-8").read().strip()
av = RLPy.RScene.GetAvatars()[0]
for cl in av.GetClothes():
    if cl.GetName() == want:
        RLPy.RFileIO.ExportObjFile(cl, os.path.join(kit.JOBS, "cloth_check.obj"), RLPy.EExport3DFileOption__None)
