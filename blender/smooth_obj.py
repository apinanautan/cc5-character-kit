# Blender (headless) helper for tools\smooth_kid.py — cleans a crumpled garment like a sculpt Smooth brush by hand.
#   blender -b --python blender\smooth_obj.py -- <in.obj> <out.obj> [iterations] [body.obj] [tight]
# 1. relax: slide points along the surface so the triangles become even (no sawtooth), the shape stays
# 2. light Taubin smoothing (no shrinking) irons small wrinkles
# 3. with body.obj (same T-pose): cloth sinking into the body is pushed out as a smooth field (both shell layers
#    move together); "tight" (shirts) also lays the cloth onto the body — inner layer GAP off the skin, outer
#    layer THICK further — so the underarm follows the body as an L instead of a web that breaks when the arm bends
# Seam copies of the same point move together; vertex order / UVs / faces are kept (CC5 ReplaceMesh needs that).
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[:2]
iterations = int(a[2]) if len(a) > 2 else 4
body = a[3] if len(a) > 3 and a[3].endswith(".obj") else None
tight = "tight" in a
over = [x[5:] for x in a if x.startswith("over=")]  # garments the shirt must lie over (the smoothed bottom)
LAMBDA, MU = 0.5, -0.53
GAP, THICK = 0.2, 0.3          # cm
NEAR, FADE = 5.0, 6.0          # tight: full lay-on within NEAR cm of the skin, fading out over FADE cm


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
key = {}
weld = [key.setdefault(tuple(round(c, 4) for c in v), len(key)) for v in vs]
pts = [None] * len(key)
for i, w in enumerate(weld):
    pts[w] = vs[i].copy()
wf = [[weld[i] for i in f] for f in fs]
nbr = [set() for _ in pts]
for f in wf:
    for i in range(len(f)):
        a_, b_ = f[i], f[(i + 1) % len(f)]
        if a_ != b_:
            nbr[a_].add(b_); nbr[b_].add(a_)


def normals(p):
    nn = [Vector() for _ in p]
    for f in wf:
        if len(f) < 3:
            continue
        fn = (p[f[1]] - p[f[0]]).cross(p[f[2]] - p[f[0]])
        for i in f:
            nn[i] += fn
    return [n.normalized() if n.length else n for n in nn]


def relax(p, times, k=0.5):
    """Tangential smoothing: even triangle sizes without changing the shape (sculpt Relax/Smooth brush)."""
    for _ in range(times):
        nn, q = normals(p), []
        for i, v in enumerate(p):
            if not nbr[i]:
                q.append(v); continue
            dlt = sum((p[j] for j in nbr[i]), Vector()) / len(nbr[i]) - v
            q.append(v + (dlt - nn[i] * dlt.dot(nn[i])) * k)
        p = q
    return p


def taubin(p, times):
    for _ in range(times):
        for k in (LAMBDA, MU):
            q = []
            for i, v in enumerate(p):
                if not nbr[i]:
                    q.append(v); continue
                c = sum((p[j] for j in nbr[i]), Vector()) / len(nbr[i])
                q.append(v + (c - v) * k)
            p = q
    return p


tree = None
if body:
    bv, bf = read(body)
    tree = BVHTree.FromPolygons(bv, bf)
over_tree = None
if over:  # the shirt is only kept outside the bottom (laying it onto the bumpy bottom crumpled the hem)
    ov_, of_ = [], []
    for o in over:
        v_, f_ = read(o)
        of_ += [[i + len(ov_) for i in f] for f in f_]
        ov_ += v_
    over_tree = BVHTree.FromPolygons(ov_, of_)
    waist = max(v.z for v in ov_)  # top of the bottom garment (CC5 OBJ is Z-up, cm)


def spread(push, times=10):
    """Spread pushes over the neighbourhood (keep the strongest) so nearby points move together."""
    for _ in range(times):
        nxt = []
        for i, d_ in enumerate(push):
            if not nbr[i]:
                nxt.append(d_); continue
            avg = sum((push[j] for j in nbr[i]), Vector()) / len(nbr[i])
            nxt.append(d_ if d_.length >= avg.length else avg)
        push = nxt
    return push


def fit(p):
    if not tree:
        return p, 0
    nn, push, n = normals(p), [], 0
    for i, v in enumerate(p):
        loc, nrm, _, dist = tree.find_nearest(v)
        if loc is None:
            push.append(Vector()); continue
        side = (v - loc).dot(nrm)
        want = GAP + (THICK if nn[i].dot(nrm) > 0 else 0.0)  # outer layer faces away from the body
        if tight and side < NEAR + FADE:
            w = 1.0 if side < NEAR else 1.0 - (side - NEAR) / FADE
            if over_tree:  # the hem stays where it was, over the bottom: lay on only above the waist
                w *= min(1.0, max(0.0, (v.z - waist - 2.0) / 5.0))
            push.append(nrm * ((want - side) * w)); n += 1
        elif side < want:
            push.append(nrm * (want - side)); n += 1
        else:
            push.append(Vector())
    if not tight:
        push = spread(push)
    p = [v + d_ for v, d_ in zip(p, push)]
    if over_tree:
        out_push = []
        for v in p:
            loc, nrm, _, dist = over_tree.find_nearest(v)
            side = (v - loc).dot(nrm) if loc is not None else 1.0
            out_push.append(nrm * (0.4 - side) if side < 0.4 and dist < 5.0 else Vector())
        p = [v + d_ for v, d_ in zip(p, spread(out_push, 6))]
    return p, n


# relax only lies flat on tight shirts; on a draped two-layer bottom it slid the inner layer through the outer
pts = relax(pts, 15 if tight else 0)
pts = taubin(pts, iterations)
pts, pushed = fit(pts)
pts = relax(pts, 8 if tight else 0)
pts = taubin(pts, 2)
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
print("SMOOTHED %d verts, avg move %.3f cm%s" % (len(vs), moved, " (tight)" if tight else ""))
print("FIT moved %d (+%d) points" % (pushed, pushed2))
