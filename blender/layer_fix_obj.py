# Blender (headless) helper for cc5\layer_fix.py — pushes the OUTER garment out past the INNER garment.
#   blender -b --python blender\layer_fix_obj.py -- <outer.obj> <inner.obj> <out.obj> [offset_cm]
# OBJ files are parsed by hand so vertex order / UVs / faces are kept exactly (CC5 ReplaceMesh needs the same topology).
# Measured and written in the posed shape (CC5 ReplaceMesh expects the current pose; bind-pose input = arms stick out).
import sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
outer_posed, inner_posed, out = a[:3]
offset = float(a[3]) if len(a) > 3 else 0.4  # OBJ units from CC5 = cm
reach = 6.0


def read(path):
    vs, fs = [], []
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.startswith("v "):
            x, y, z = map(float, line.split()[1:4])
            vs.append(Vector((x, y, z)))
        elif line.startswith("f "):
            fs.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    return vs, fs


ov, of = read(outer_posed)
iv, ifc = read(inner_posed)
# CC5 OBJ (no AxisYUp flag) is Z-up: height is Z, "horizontal" is X/Y
bvh = BVHTree.FromPolygons(iv, ifc)
cx = sum(v.x for v in iv) / len(iv)
cy = sum(v.y for v in iv) / len(iv)
zlo, zhi = min(v.z for v in iv), max(v.z for v in iv)


def last_hit(p, d):
    far, start, travelled = None, p.copy(), 0.0
    while travelled < reach:
        loc, nrm, _, dist = bvh.ray_cast(start, d, reach - travelled)
        if loc is None:
            break
        far = loc
        travelled += dist + 1e-3
        start = loc + d * 1e-3
    return far


disp = [Vector() for _ in ov]
moved = 0
for i, p in enumerate(ov):
    if not (zlo - 1 <= p.z <= zhi + 1):
        continue
    d = Vector((p.x - cx, p.y - cy, 0.0))
    if d.length < 1e-6:
        continue
    d.normalize()
    hit = last_hit(p, d)
    if hit is not None:
        disp[i] = (hit + d * offset) - p
        moved += 1

# fade the push into the untouched part (no step line where the pushed band ends)
from mathutils.kdtree import KDTree
FADE = 8.0  # cm
pushed = [i for i, dv in enumerate(disp) if dv.length > 0]
if pushed:
    kd = KDTree(len(pushed))
    for k, i in enumerate(pushed):
        kd.insert(ov[i], k)
    kd.balance()
    for i, p in enumerate(ov):
        if disp[i].length > 0:
            continue
        co, k, dist = kd.find(p)
        if dist < FADE:
            w = (1.0 - dist / FADE) ** 2
            disp[i] = disp[pushed[k]] * w

nbr = [set() for _ in ov]
for f in of:
    for k in range(len(f)):
        x, y = f[k], f[(k + 1) % len(f)]
        nbr[x].add(y); nbr[y].add(x)
for _ in range(6):  # spread the push so the hem stays smooth; never pull a pushed vertex back in
    new = []
    for i, dv in enumerate(disp):
        if nbr[i]:
            avg = sum((disp[j] for j in nbr[i]), Vector()) / len(nbr[i])
            new.append(dv if dv.length >= avg.length else dv * 0.5 + avg * 0.5)
        else:
            new.append(dv)
    disp = new

# second pass, seen from the INNER garment: small parts (belt loops, fly, folds) that stick out between the outer
# garment's vertices still show through -> pull those INNER points back under the outer garment (hidden there, so
# the outer garment stays smooth). Written to <out>_inner.obj; cc5\layer_fix.py replaces the inner mesh with it.
np_ = [ov[i] + disp[i] for i in range(len(ov))]
obvh = BVHTree.FromPolygons(np_, of)
idisp = [Vector() for _ in iv]
under = [False] * len(iv)
pokes = 0
for k, q in enumerate(iv):
    d = Vector((q.x - cx, q.y - cy, 0.0))
    if d.length < 1e-6:
        continue
    d.normalize()
    inside = obvh.ray_cast(q - d * reach, d, reach * 2)  # first outer surface along the line, from the centre side
    out_hit = obvh.ray_cast(q + d * 0.01, d, reach)
    back = obvh.ray_cast(q, -d, reach)
    under[k] = out_hit[0] is not None or back[0] is not None
    if out_hit[0] is None and back[0] is not None:  # outer garment is inside this point: it pokes through
        idisp[k] = (back[0] - d * offset) - q
        pokes += 1
inbr = [set() for _ in iv]
for f in ifc:
    for k in range(len(f)):
        x, y = f[k], f[(k + 1) % len(f)]
        inbr[x].add(y); inbr[y].add(x)
for _ in range(3):  # soften around the pulled points, only where the outer garment covers it
    new = []
    for i, dv in enumerate(idisp):
        if under[i] and inbr[i]:
            avg = sum((idisp[j] for j in inbr[i]), Vector()) / len(inbr[i])
            new.append(dv if dv.length >= avg.length else dv * 0.5 + avg * 0.5)
        else:
            new.append(dv)
    idisp = new
print("POKES", pokes)
if pokes:
    vi = 0
    with open(out[:-4] + "_inner.obj", "w", encoding="utf-8") as w:
        for line in open(inner_posed, encoding="utf-8", errors="ignore"):
            if line.startswith("v "):
                p = iv[vi] + idisp[vi]
                rest = line.split()[4:]
                w.write("v %.6f %.6f %.6f%s\n" % (p.x, p.y, p.z, (" " + " ".join(rest)) if rest else ""))
                vi += 1
            else:
                w.write(line)

vi = 0
with open(out, "w", encoding="utf-8") as w:
    for line in open(outer_posed, encoding="utf-8", errors="ignore"):
        if line.startswith("v "):
            p = ov[vi] + disp[vi]  # CC5 ReplaceMesh takes the CURRENT-pose shape
            rest = line.split()[4:]  # keep vertex colours if any
            w.write("v %.6f %.6f %.6f%s\n" % (p.x, p.y, p.z, (" " + " ".join(rest)) if rest else ""))
            vi += 1
        else:
            w.write(line)
print("MOVED", moved, "of", len(ov))
print("WROTE", out)
