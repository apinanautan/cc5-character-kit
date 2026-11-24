# Inside CC5 via bridge: set UV Tiling for ONE texture channel by driving CC5's own Modify > Texture Settings panel.
# Needed because RLPy AddUvDataKey cannot reach the PBR Roughness channel (enum 16 > Quantity 15 -> error).
# Requires: the cloth selected and the Modify > Material tab open (Texture Settings visible).
# args: channel=Roughness  tile=25  [expect=<substring of bitmap path, for safety>]
import RLPy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle
try:
    from PySide2 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
A = BRIDGE_ARGS  # noqa
app = QtWidgets.QApplication.instance(); log = []


def vis(name, cls=QtWidgets.QWidget):
    ws = [w for w in app.allWidgets() if w.objectName() == name and isinstance(w, cls) and w.isVisible()]
    if not ws: raise RuntimeError("widget %s not visible - open Modify > Material > Texture Settings with the cloth selected" % name)
    return ws[0]


def click(w):
    p = QtCore.QPointF(w.width() / 2, w.height() / 2); g = QtCore.QPointF(w.mapToGlobal(p.toPoint()))
    for t in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonRelease):
        app.sendEvent(w, QtGui.QMouseEvent(t, p, g, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier))
    settle(400)


def path(): return vis("qtBipmapPathLineEdit", QtWidgets.QLineEdit).text()


def tiling(): return vis("qtUTilingDEXSpinBox", QtWidgets.QDoubleSpinBox).value(), vis("qtVTilingDSpinBox", QtWidgets.QDoubleSpinBox).value()


ch = A.get("channel", "Roughness"); T = float(A.get("tile", 25))
allch = vis("qtAffectAllChannelsCheckBox", QtWidgets.QCheckBox)
if allch.isChecked(): allch.setChecked(False); settle(200); log.append("unticked Affect All Channels")
click(vis("qt%sLabel" % ch, QtWidgets.QLabel))
log.append("selected %s bitmap=%s tiling=%s" % (ch, os.path.basename(path()), tiling()))
if A.get("expect") and A["expect"].lower() not in path().lower(): raise RuntimeError("wrong channel selected: " + path())
for nm in ("qtUTilingDEXSpinBox", "qtVTilingDSpinBox"):
    sb = vis(nm, QtWidgets.QDoubleSpinBox)
    sb.setFocus(); sb.lineEdit().selectAll(); sb.lineEdit().setText(str(T))
    for t in (QtCore.QEvent.KeyPress, QtCore.QEvent.KeyRelease):
        app.sendEvent(sb.lineEdit(), QtGui.QKeyEvent(t, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier))
    sb.editingFinished.emit(); settle(300)
# read back: hop to Base Color and back, the panel must still show T for this channel
click(vis("qtDiffuseLabel", QtWidgets.QLabel)); d = tiling()
click(vis("qt%sLabel" % ch, QtWidgets.QLabel)); r = tiling()
log.append("readback diffuse=%s %s=%s" % (d, ch, r))
if r != (T, T): raise RuntimeError("tiling did not stick: " + "; ".join(log))
if d != (1.0, 1.0): log.append("WARNING diffuse tiling is %s" % (d,))
BRIDGE_RESULT = "; ".join(log)
