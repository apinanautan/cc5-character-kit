# CC5 half of tools\smooth_kid.py (crumpled adult clothes on a kid): never runs Blender itself, so CC5 and
# Blender are never heavy at the same time (that combination blue-screened this PC, bugcheck 0x1A).
#   step=export: T-pose, write every garment c<n>.obj and the bare body body.obj into <job>\smooth\
#   step=apply : T-pose, put the smoothed c<n>_s.obj back (ReplaceMesh), A-pose, render <name>.png, save project
#   tools\cc5.py run cc5\smooth_cloth.py job=<job dir> step=export|apply
import json, os
import RLPy

A = BRIDGE_ARGS  # noqa: F821
POSE = os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose", "Calibration")
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
work = os.path.join(d, "smooth")
os.makedirs(work, exist_ok=True)
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSE, "T-Pose.rlPose"))
log = []
if A["step"] == "export":
    for f in os.listdir(work):
        os.remove(os.path.join(work, f))
    for n, cl in enumerate(av.GetClothes()):
        RLPy.RFileIO.ExportObjFile(cl, os.path.join(work, "c%d.obj" % n), RLPy.EExport3DFileOption__None)
        log.append("c%d %s" % (n, cl.GetName()))
    for o in list(av.GetClothes()) + list(av.GetHairs()) + list(av.GetAccessories()):
        RLPy.RScene.RemoveObject(o)  # not saved: only for the body OBJ
    RLPy.RFileIO.ExportObjFile(av, os.path.join(work, "body.obj"), RLPy.EExport3DFileOption__None)
else:
    for n, cl in enumerate(av.GetClothes()):
        f = os.path.join(work, "c%d_s.obj" % n)
        if os.path.exists(f):
            cl.GetMeshes()[0].ReplaceMesh(f, RLPy.EReplaceMeshOption_ZUp, False)
            log.append("replaced c%d %s" % (n, cl.GetName()))
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(os.path.join(POSE, "A-Pose.rlPose"))
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    for _ in range(2):
        RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
BRIDGE_RESULT = "\n".join(log)
