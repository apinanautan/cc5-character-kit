"""Find the button bumps that the AI sculpted on the garment front, so real buttons can be placed there.
Bump = vertex sticking out of a heavily smoothed copy of the surface, on the front, near the centre line.
  python buttons_detect.py --run <run> --mesh final.obj [--out buttons.json]
Writes buttons.json: [{"pos":[x,y,z], "normal":[...], "radius":r}] in the mesh's Y-up cm (front = +Z)."""
import argparse, json
from pathlib import Path
import numpy as np, trimesh, scipy.sparse as sp
from scipy.sparse.csgraph import connected_components

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--mesh", default="final.obj")
ap.add_argument("--out", default="buttons.json"); ap.add_argument("--thr", type=float, default=0.12)
ap.add_argument("--iters", type=int, default=25); ap.add_argument("--max_n", type=int, default=6)
a = ap.parse_args(); run = Path(a.run)
m = trimesh.load(run / a.mesh, force="mesh", process=False)
V, N = m.vertices, m.vertex_normals; E = m.edges_unique; n = len(V)
A = sp.coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
deg = np.asarray(A.sum(1)).ravel()
S = V.copy()
for _ in range(a.iters): S = (A @ S) / np.maximum(deg, 1)[:, None]
d = np.einsum("ij,ij->i", V - S, N)                                   # how far each vertex sticks out
lo, hi = V.min(0), V.max(0); H = hi[1] - lo[1]
front = N[:, 2] > 0.55
zmax_at = V[:, 2] > np.percentile(V[front, 2], 40) if front.any() else front
cx = np.median(V[front & (V[:, 1] > lo[1] + 0.3 * H), 0])
cand = front & zmax_at & (np.abs(V[:, 0] - cx) < 0.09 * (hi[0] - lo[0])) & (d > a.thr) \
       & (V[:, 1] > lo[1] + 0.03 * H) & (V[:, 1] < hi[1] - 0.12 * H)
idx = np.flatnonzero(cand)
sub = A[idx][:, idx]; k, lab = connected_components(sub, directed=False)
out = []
for c in range(k):
    vi = idx[lab == c]
    if len(vi) < 15: continue
    w = d[vi]; p = (V[vi] * w[:, None]).sum(0) / w.sum(); nrm = (N[vi] * w[:, None]).sum(0); nrm /= np.linalg.norm(nrm)
    r = float(np.percentile(np.linalg.norm(V[vi] - p, axis=1), 90))
    if not (0.35 < r < 1.6): continue                                   # cm: button sized blobs only
    out.append(dict(pos=p.tolist(), normal=nrm.tolist(), radius=r, height=float(w.max()), verts=int(len(vi))))
out = sorted(out, key=lambda b: -b["height"] * b["verts"])[:a.max_n]
out = sorted(out, key=lambda b: -b["pos"][1])
# buttons on one shirt are the same size and sit on one line: use the median radius, drop far-off ones
if out:
    rm = float(np.median([b["radius"] for b in out])); xm = float(np.median([b["pos"][0] for b in out]))
    out = [dict(b, radius=rm) for b in out if abs(b["pos"][0] - xm) < 2.5]
json.dump(out, open(run / a.out, "w"), indent=1)
print(json.dumps(dict(centre_x=float(cx), found=len(out), buttons=[[round(v, 2) for v in b["pos"]] + [round(b["radius"], 2)] for b in out])))
