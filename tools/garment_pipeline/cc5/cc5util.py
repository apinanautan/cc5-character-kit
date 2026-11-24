import os
import RLPy
try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore
POSES = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"

def settle(ms):
    loop = QtCore.QEventLoop(); QtCore.QTimer.singleShot(ms, loop.quit)
    (getattr(loop, "exec", None) or loop.exec_)()

def pose(av, name):
    RLPy.RScene.SelectObject(av)
    p = name if os.path.isabs(name) else os.path.join(POSES, name + ".rlPose")
    if RLPy.RFileIO.LoadFile(p).IsError(): raise RuntimeError("pose failed " + p)
    settle(400)

def save_character(av, path):
    if os.path.exists(path): raise RuntimeError("refuse to overwrite " + path)
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    r = RLPy.RFileIO.SaveFile(av, s, path)
    if r.IsError() or not os.path.exists(path): raise RuntimeError("save failed " + path)

def shot(path, loc=RLPy.ECameraLocationType_Front):
    cam = RLPy.RScene.GetCurrentCamera()
    cam.SetCameraLocation(loc); settle(300)
    RLPy.RGlobal.RenderImage(path)
    if loc != RLPy.ECameraLocationType_Front:          # never leave the user's viewport looking at the back
        cam.SetCameraLocation(RLPy.ECameraLocationType_Front); settle(100)
