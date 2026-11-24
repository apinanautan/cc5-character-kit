"""Let CC5 finish asynchronous material loading before capturing an output."""

from pathlib import Path
from tempfile import TemporaryDirectory

import RLPy
try:
    from PySide2 import QtCore, QtGui
except ImportError:
    from PySide6 import QtCore, QtGui


def settle(ms):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    (getattr(loop, "exec", None) or loop.exec_)()


def signature(path):
    image = QtGui.QImage(str(path))
    if image.isNull():
        raise RuntimeError(f"CC5 did not write a texture-check frame: {path}")
    image = image.scaled(96, 96)
    return tuple(image.pixel(x, y) for y in range(image.height()) for x in range(image.width()))


def stable(previous, current):
    if len(previous) != len(current) or not current:
        return False
    changed = 0
    for before, after in zip(previous, current):
        if any(abs(((before >> shift) & 255) - ((after >> shift) & 255)) > 7
               for shift in (0, 8, 16)):
            changed += 1
    return changed * 1000 <= len(current)


def wait_for_textures(scratch=None):
    """Warm up for 15 seconds, then require two stable frame comparisons."""
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    settle(15000)
    with TemporaryDirectory(prefix="cc5-texture-check-", dir=scratch if scratch and Path(scratch).is_dir() else None) as tmp:
        previous = ()
        matches = 0
        for index in range(10):
            probe = Path(tmp) / f"check_{index}.png"
            RLPy.RGlobal.RenderImage(str(probe))
            current = signature(probe)
            matches = matches + 1 if stable(previous, current) else 0
            if matches == 2:
                return index + 1
            previous = current
            settle(3000)
    raise RuntimeError("CC5 texture-check frames did not stabilize; output was not captured")
