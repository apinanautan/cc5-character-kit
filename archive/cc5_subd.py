# Run inside CC5: switch the character to its highest SubD level (max 2) and render a front test image.
import os, RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
av = RLPy.RScene.GetAvatars()[0]
lvl = min(2, av.GetMaxSubdivMeshLevel())
av.SwitchSubdivMeshLevel(lvl)
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(J, "subd_test.png"))
open(os.path.join(J, "subd_log.txt"), "w").write("max=%s now=%s" % (av.GetMaxSubdivMeshLevel(), av.GetSubdivMeshLevel()))
