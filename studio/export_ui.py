# Export the character that is open in CC5 as .iAvatar by driving CC5's menus (CC5 has no Python call for it):
# File > Export > iAvatar > Export > paste the full path > Enter. Same clicks as by hand, scaled to the screen.
# CC5 must be maximized on the main screen; don't use the mouse while it runs (~10 s + the save itself).
import ctypes, os, shutil, subprocess, time
from ctypes import wintypes

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    u32.SetProcessDPIAware()

BASE_W, BASE_H = 1456, 819  # the frame the click points were measured in (full screen, CC5 maximized)
FILE, EXPORT, IAVATAR, OK_BTN, NAME_BOX = (13, 30), (62, 200), (314, 203), (654, 576), (600, 663)


def cc5_window():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CharacterCreator.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    pids = {int(l.split('","')[1]) for l in out.splitlines() if l.startswith('"CharacterCreator')}
    best = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u32.IsWindowVisible(h):
            n = u32.GetWindowTextLengthW(h)
            b = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(h, b, n + 1)
            if b.value.startswith("Character Creator"):
                best.append(h)
        return True

    u32.EnumWindows(cb, 0)
    return best[0] if best else None


def front(h):
    u32.ShowWindow(h, 3)  # maximize
    u32.keybd_event(0x12, 0, 0, 0); u32.keybd_event(0x12, 0, 2, 0)  # Alt tap lets us take the foreground
    u32.SetForegroundWindow(h)
    time.sleep(0.8)


def click(pt):
    sw, sh = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
    x, y = int(pt[0] * sw / BASE_W), int(pt[1] * sh / BASE_H)
    u32.SetCursorPos(x, y)
    time.sleep(0.15)
    u32.mouse_event(2, 0, 0, 0, 0); u32.mouse_event(4, 0, 0, 0, 0)


def key(*vks):
    for v in vks:
        u32.keybd_event(v, 0, 0, 0)
    for v in reversed(vks):
        u32.keybd_event(v, 0, 2, 0)
    time.sleep(0.15)


def set_clipboard(text):
    k32.GlobalAlloc.restype = wintypes.HGLOBAL
    k32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    u32.SetClipboardData.restype = wintypes.HANDLE
    u32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    u32.OpenClipboard.argtypes = [wintypes.HWND]
    data = ctypes.create_unicode_buffer(text)
    size = ctypes.sizeof(data)
    for _ in range(10):
        if u32.OpenClipboard(None):
            break
        time.sleep(0.2)
    u32.EmptyClipboard()
    hmem = k32.GlobalAlloc(0x0042, size)
    ctypes.memmove(k32.GlobalLock(hmem), data, size)
    k32.GlobalUnlock(hmem)
    u32.SetClipboardData(13, hmem)
    u32.CloseClipboard()


def wait_file(path, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(path):
            s = os.path.getsize(path)
            time.sleep(4)
            if s > 0 and os.path.getsize(path) == s:
                return True
        time.sleep(2)
    return False


def export(target, backup_dir):
    """Export the open CC5 character to target (.iAvatar). An old file is moved to backup_dir first
    (so CC5 never asks 'replace?'). Returns (ok, message)."""
    h = cc5_window()
    if not h:
        return False, "ไม่เจอหน้าต่าง CC5"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if os.path.exists(target):
        os.makedirs(backup_dir, exist_ok=True)
        shutil.move(target, os.path.join(backup_dir, "old_" + time.strftime("%Y%m%d_%H%M%S_") + os.path.basename(target)))
    set_clipboard(target)
    front(h)
    click(FILE); time.sleep(1)
    click(EXPORT); time.sleep(1)
    click(IAVATAR); time.sleep(3)
    click(OK_BTN); time.sleep(4)
    click(NAME_BOX); time.sleep(0.3)
    key(0x11, 0x41)  # Ctrl+A
    key(0x11, 0x56)  # Ctrl+V
    key(0x0D)        # Enter
    if wait_file(target):
        return True, "%d MB" % (os.path.getsize(target) // 1048576)
    key(0x1B); key(0x1B)
    return False, "ไม่ได้ไฟล์ iAvatar (เมนู CC5 อาจไม่ตรงตำแหน่ง)"
