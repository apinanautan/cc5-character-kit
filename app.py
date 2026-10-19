# CC5 Character Studio: paste a story's character list -> each character goes step by step to a finished .iAvatar.
#   python app.py   (or double-click "CC5 Character Studio" on the Desktop)
# Opens the interface (studio/ui/index.html) in its own app window; closing that window ends the program.
import os, subprocess, sys, webbrowser

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "studio")]
import kit
import web

BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]


def main():
    srv, port = web.serve()
    url = "http://127.0.0.1:%d/" % port
    exe = next((b for b in BROWSERS if os.path.exists(b)), None)
    if not exe:
        webbrowser.open(url)
        input("เปิดในเบราว์เซอร์แล้ว — กด Enter เพื่อปิดโปรแกรม")
        return
    profile = os.path.join(kit.DATA, "cc5_studio_window")  # own profile: the window is its own process we can wait on
    p = subprocess.Popen([exe, "--app=" + url, "--user-data-dir=" + profile, "--window-size=1440,900",
                          "--no-first-run", "--no-default-browser-check"])
    p.wait()
    if web.busy():  # window closed while working: keep going in the background until this character's step ends
        web.STATE["runner"].stop = True
        web.STATE["thread"].join()


if __name__ == "__main__":
    main()
