"""Fabric picture helpers.
  .venv\\Scripts\\python.exe tile_texture.py --invert <weave.png> <out.png>      same picture, colours inverted (for Metallic)
  .venv\\Scripts\\python.exe tile_texture.py <in.png> <out.png> [N=25] [size=4096] [gray=1]
      repeat N x N into one image. NOT recommended any more: CC5 showed it as flat grey; use real Tiling 25 instead
      (cc5/set_channel_tiling_ui.py)."""
import sys
from PIL import Image, ImageOps
if sys.argv[1] == "--invert":
    ImageOps.invert(Image.open(sys.argv[2]).convert("L")).save(sys.argv[3]); print("WROTE", sys.argv[3]); sys.exit()
src, dst = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 25
S = int(sys.argv[4]) if len(sys.argv) > 4 else 4096
im = Image.open(src).convert("L" if (sys.argv[5] if len(sys.argv) > 5 else "1") == "1" else "RGB")
t = round(S / N); tile = im.resize((t, t), Image.LANCZOS)
out = Image.new(im.mode, (t * N, t * N))
for i in range(N):
    for j in range(N): out.paste(tile, (i * t, j * t))
out.resize((S, S), Image.LANCZOS).save(dst); print("WROTE", dst, N, "x", N)
