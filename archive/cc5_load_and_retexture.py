# Run inside CC5: open load_one.txt project, then apply retexture.json and render retexture_test.png
import os
H = os.path.dirname(os.path.abspath(__file__))
for s in ("cc5_load_one.py", "cc5_retexture.py"):
    p = os.path.join(H, s)
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"), {"__file__": p, "__name__": "__main__"})
