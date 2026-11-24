# Copy chosen exported .iAvatar files from Desktop\<story>\<n>\ into the story's character folder on Google Drive (only .iAvatar).
# The Drive file being replaced is first copied to runs\drive_backup\<date>\ (never deleted).
#   python tools\push_to_drive.py <story> <name1> <name2> ...      e.g. ดวงเมียน้อย นาวีชุดนักศึกษา วินัยตำรวจ
import os, shutil, sys, time
story, names = sys.argv[1], [n.replace(".iAvatar", "") for n in sys.argv[2:]]
D = os.path.join(os.path.expanduser("~"), "Desktop", story)
G = os.path.join(r"G:\ไดรฟ์ของฉัน", story, story + " ตัวละคร")
BK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs", "drive_backup", time.strftime("%Y%m%d"))
os.makedirs(BK, exist_ok=True)
src = {f: os.path.join(dp, f) for dp, dn, fn in os.walk(D) for f in fn if f.lower().endswith(".iavatar")}
dst = {f: os.path.join(dp, f) for dp, dn, fn in os.walk(G) for f in fn if f.lower().endswith(".iavatar")}
for n in names:
    f = n + ".iAvatar"
    if f not in src or f not in dst:
        print("SKIP (not found on Desktop or in Drive):", f); continue
    shutil.copy2(dst[f], os.path.join(BK, f))                       # backup of the Drive version
    shutil.copy2(src[f], dst[f] + ".tmp"); os.replace(dst[f] + ".tmp", dst[f])
    print("OK", f, "->", os.path.relpath(os.path.dirname(dst[f]), G), "(%d MB)" % (os.path.getsize(dst[f]) // 1048576), flush=True)
