# Run inside CC5 (Somjit 70 loaded): save the arm diffuse -> krong_somjit_70\arm_diffuse.png
import os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
av = RLPy.RScene.GetAvatars()[0]
comp = av.GetMaterialComponent()
img = comp.GetImage("CC_Base_Body", "Std_Skin_Arm", RLPy.EMaterialTextureChannel_Diffuse)
r = img.SaveFile(os.path.join(J, "krong_somjit_70", "arm_diffuse.png"))
open(os.path.join(J, "skin_probe.txt"), "w", encoding="utf-8").write("save %r" % (r,))
