# Export the character that is open in CC5 to Desktop\<story>\<folder>\<name>.iAvatar (the old file is moved to a backup folder, never deleted).
#   python tools\export_open.py <story folder on Desktop> <sub folder> <file name without .iAvatar> <job dir name for the backup>
# CC5 must be maximized and in front; don't touch the mouse while it runs (~1 min).
import os, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root); os.chdir(root)
from studio import export_ui
story, sub, name, job = sys.argv[1:5]
base = os.path.join(r"G:\ไดรฟ์ของฉัน", story, story + " ตัวละคร") if "drive" in sys.argv[5:] else os.path.join(os.path.expanduser("~"), "Desktop", story)
dest = os.path.join(base, sub, name + ".iAvatar")
backup = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", job, "old_exports")
print(export_ui.export(dest, backup), flush=True)
