"""Stage 4a+: fit an already placed garment snugly onto the T-pose body BEFORE skin weights.
  python fit.py --run <run> --placed placed_hy_v3.obj --body body_tpose.obj --out fitted_hy [--ease 0.5]
1) search width/depth stretch (sx, sy) and front/back shift so the shirt wraps the torso with least penetration
2) push every vertex still under the skin out along the body normal to <ease> cm, with the push smoothed over the
   mesh so the cloth moves as a sheet (no spikes) and its thickness is kept. Writes <out>.obj (Y-up cm) + report."""
import argparse, json
from pathlib import Path
import numpy as np, trimesh, scipy.sparse as sp
from scipy.spatial import cKDTree
from place import load_body

ap = argparse.ArgumentParser()
for k in ("run", "placed", "body", "out"): ap.add_argument("--" + k, required=True)
ap.add_argument("--ease", type=float, default=0.5); ap.add_argument("--max_stretch", type=float, default=1.3)
a = ap.parse_args(); run = Path(a.run)
body = load_body(a.body); bv, bn = body.vertices, body.vertex_normals; bt = cKDTree(bv)
g = trimesh.load(run / a.placed, force="mesh", process=False)
P0 = np.c_[g.vertices[:, 0], -g.vertices[:, 2], g.vertices[:, 1]]          # Y-up -> Z-up
cen = P0.mean(0)

def sd_of(P):
    d, i = bt.query(P); return np.einsum("ij,ij->i", P - bv[i], bn[i]), i

def stats(P):
    s, _ = sd_of(P); return dict(inside_frac=float((s < 0).mean()), inside_p99=float(np.percentile(np.clip(-s, 0, None), 99)),
                                 median_gap=float(np.median(s)), floating_frac=float((s > 4).mean()))
rng = np.random.default_rng(0); smp = rng.choice(len(P0), 20000, replace=False)

def tf(p, P):
    sx, sy, ty = p; return (P - cen) * [sx, sy, 1] + cen + [0, ty, 0]

def cost(p):
    s, _ = sd_of(tf(p, P0[smp])); return (np.clip(a.ease - s, 0, None) ** 2).mean() * 50 + (np.clip(s - 3, 0, None) ** 2).mean()
x = [1.0, 1.0, 0.0]; best = cost(x)
for step in (0.04, 0.02, 0.01):
    for _ in range(10):
        moved = False
        for i in range(3):
            for sg in (1, -1):
                y = list(x); y[i] += sg * (step if i < 2 else step * 50)
                c = cost(y)
                if c < best and max(y[0], y[1]) <= a.max_stretch: x, best, moved = y, c, True
        if not moved: break
P = tf(x, P0); before = stats(P)
# smoothed push-out (the sheet moves together; inner + outer walls keep their spacing)
E = g.edges_unique; n = len(P)
A = sp.coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
deg = np.asarray(A.sum(1)).ravel() + 1
for it in range(6):
    s, i = sd_of(P)
    push = np.clip(a.ease - s, 0, None)[:, None] * bn[i]
    for _ in range(15): push = (A @ push + push) / deg[:, None]      # spread the push to neighbours
    s2, i2 = sd_of(P + push)
    hard = np.clip(a.ease - s2, 0, None)[:, None] * bn[i2]                 # whatever is still under the skin
    P = P + push + hard
after = stats(P)
trimesh.Trimesh(np.c_[P[:, 0], P[:, 2], -P[:, 1]], g.faces, process=False).export(run / (a.out + ".obj"))
rep = dict(stretch_sx_sy_ty=x, before=before, after=after, faces=int(len(g.faces)))
json.dump(rep, open(run / (a.out + "_report.json"), "w"), indent=1); print(json.dumps(rep))
