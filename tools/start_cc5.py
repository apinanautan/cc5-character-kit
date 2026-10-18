# Start CC5 unattended: launches it (unless running), presses Enter on its small startup popups
# ("Failed to establish a connection" -> OK, "Unsaved project data found" -> default) via window messages
# (works even when CC5 is not in front), then waits until the CC5Bridge heartbeat is alive.
#   python tools\start_cc5.py [--restart]
import ctypes, os, subprocess, sys, time
from ctypes import wintypes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

EXE = r"C:\Program Files\Reallusion\Character Creator 5\Bin64\CharacterCreator.exe"
u32 = ctypes.windll.user32
WM_KEYDOWN, WM_KEYUP, VK_RETURN, VK_ESCAPE = 0x100, 0x101, 0x0D, 0x1B


def cc5_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CharacterCreator.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return {int(l.split('","')[1]) for l in out.splitlines() if l.startswith('"CharacterCreator')}


def popups(pids):
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        pid = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in pids and u32.IsWindowVisible(h):
            r = wintypes.RECT()
            u32.GetWindowRect(h, ctypes.byref(r))
            w, hgt = r.right - r.left, r.bottom - r.top
            if 150 < w < 700 and 80 < hgt < 400:  # small dialog, not the main window / splash
                found.append(h)
        return True

    u32.EnumWindows(cb, 0)
    return found


def press(h, vk):
    u32.PostMessageW(h, WM_KEYDOWN, vk, 0)
    u32.PostMessageW(h, WM_KEYUP, vk, 0)


def main():
    if "--restart" in sys.argv and cc5_pids():
        subprocess.run(["taskkill", "/IM", "CharacterCreator.exe", "/F"], capture_output=True)
        time.sleep(4)
    if not cc5_pids():
        subprocess.Popen([EXE])
    hb = os.path.join(kit.JOBS, "bridge", "heartbeat.txt")
    t0 = time.time()
    while time.time() - t0 < 600:
        pids = cc5_pids()
        for h in popups(pids):
            press(h, VK_RETURN)  # OK on "Failed to establish..."; default button elsewhere
        if os.path.exists(hb) and time.time() - os.path.getmtime(hb) < 10 and time.time() - t0 > 20:
            time.sleep(5)  # let late popups appear, then clear them once more
            for h in popups(cc5_pids()):
                press(h, VK_ESCAPE)  # "Unsaved project data found" -> Cancel
            print("CC5 ready (bridge alive) after %.0fs" % (time.time() - t0))
            return
        time.sleep(3)
    sys.exit("CC5 did not become ready in 10 min")


if __name__ == "__main__":
    main()
