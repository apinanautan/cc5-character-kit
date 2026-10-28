# Blender (headless) helper for cc5\smooth_cloth.py — irons out crumpled cloth (adult garment squeezed onto a kid).
#   blender -b --python blender\smooth_obj.py -- <in.obj> <out.obj> [iterations] [body.obj]
# Taubin smoothing (shrink + inflate each pass) removes small wrinkles without shrinking the garment.
# With body.obj (same pose, T-pose) it also fits the cloth to the body like a sculpt Smooth brush by hand:
# skin poking through is pushed out to GAP, cloth hanging far off the (kid's) body is drawn in a little.
# Seam copies of the same point move together; vertex order / UVs / faces are kept (CC5 ReplaceMesh needs that).
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[:2]
iterations = int(a[2]) if len(a) > 2 else 12
body = a[3] if len(a) > 3 else None
LAMBDA, MU = 0.5, -0.53
GAP, LOOSE, PULL = 0.4, 2.5, 0.35  # cm: min distance off the skin; beyond LOOSE draw PULL of the extra in


def read(path):
    vs, fs = [], []
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.startswith("v "):
            vs.append(Vector(map(float, line.split()[1:4])))
        elif line.startswith("f "):
            fs.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    return vs, fs


lines = open(src, encoding="utf-8", errors="ignore").read().splitlines()
vs, fs = read(src)

# weld by position: one smoothing point per spot, so split seams don't open up
key = {}
weld = [key.setdefault(tuple(round(c, 4) for c in v), len(key)) for v in vs]
pts = [None] * len(key)
for i, w in enumerate(weld):
    pts[w] = vs[i].copy()
nbr = [set() for _ in pts]
for f in fs:
    for i in range(len(f)):
        a_, b_ = weld[f[i]], weld[f[(i + 1) % len(f)]]
        if a_ != b_:
            nbr[a_].add(b_); nbr[b_].add(a_)


def step(p, k):
    q = []
    for i, v in enumerate(p):
        if not nbr[i]:
            q.append(v); continue
        c = sum((p[j] for j in nbr[i]), Vector()) / len(nbr[i])
        q.append(v + (c - v) * k)
    return q


tree = None
if body:
    bv, bf = read(body)
    tree = BVHTree.FromPolygons(bv, bf)


def fit(p):
    if not tree:
        return p, 0
    out_, n = [], 0
    for v in p:
        loc, nrm, _, dist = tree.find_nearest(v)
        if loc is None:
            out_.append(v); continue
        side = (v - loc).dot(nrm)
        if side < GAP:                      # inside the body or touching: out to GAP
            v = loc + nrm * GAP; n += 1
        elif side > LOOSE:                  # baggy: draw in toward the body
            v = v - nrm * ((side - LOOSE) * PULL)
        out_.append(v)
    return out_, n


for _ in range(iterations):
    pts = step(step(pts, LAMBDA), MU)
pts, pushed = fit(pts)
for _ in range(2):                          # settle the fitted surface
    pts = step(step(pts, LAMBDA), MU)
pts, pushed2 = fit(pts)
moved = sum((pts[weld[i]] - vs[i]).length for i in range(len(vs))) / max(1, len(vs))
n = 0
with open(out, "w", encoding="utf-8") as w:
    for line in lines:
        if line.startswith("v "):
            rest = line.split()[4:]
            p = pts[weld[n]]; n += 1
            w.write("v %.6f %.6f %.6f%s\n" % (p.x, p.y, p.z, (" " + " ".join(rest)) if rest else ""))
        else:
            w.write(line + "\n")
print("SMOOTHED %d verts, avg move %.3f cm" % (len(vs), moved))
print("FIT pushed out %d (+%d) points" % (pushed, pushed2))
