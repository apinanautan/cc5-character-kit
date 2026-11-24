"""After the Blender push: keep the ORIGINAL surface detail, apply only a smoothed version of the push.
The cloth sim moves vertices by ~1-3 cm but also adds small crinkles; here displacement = pushed - tight is
smoothed over the mesh, so the shirt keeps its own clean surface and just moves out as a sheet.
  python smooth_push.py --run <run> --tight tight.obj --pushed pushed.obj --body body_tpose.obj --out final"""
import argparse, json
from pathlib import Path
import numpy as np, trimesh, scipy.sparse as sp
from scipy.spatial import cKDTree
from place import load_body

ap = argparse.ArgumentParser()
for k in ("run", "tight", "pushed", "body", "out"): ap.add_argument("--" + k, required=True)
ap.add_argument("--iters", type=int, default=30)
a = ap.parse_args(); run = Path(a.run)
T = trimesh.load(run / a.tight, force="mesh", process=False)
Pp = trimesh.load(run / a.pushed, force="mesh", process=False).vertices
assert len(Pp) == len(T.vertices)
D = Pp - T.vertices
E = T.edges_unique; n = len(D)
A = sp.coo_matrix((np.ones(len(E) * 2), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
deg = np.asarray(A.sum(1)).ravel() + 1
Ds = D.copy()
for _ in range(a.iters): Ds = (A @ Ds + Ds) / deg[:, None]
F = T.vertices + Ds
body = load_body(a.body); bv, bn = body.vertices, body.vertex_normals; bt = cKDTree(bv)
def inside(V):                                     # V is Y-up; body is Z-up
    Z = np.c_[V[:, 0], -V[:, 2], V[:, 1]]; _, i = bt.query(Z); s = np.einsum("ij,ij->i", Z - bv[i], bn[i])
    return float((s < 0).mean()), float(np.percentile(np.clip(-s, 0, None), 99))
trimesh.Trimesh(F, T.faces, process=False).export(run / (a.out + ".obj"))
rep = dict(inside_pushed=inside(Pp), inside_final=inside(F), move_median_cm=float(np.median(np.linalg.norm(Ds, axis=1))))
json.dump(rep, open(run / (a.out + "_report.json"), "w"), indent=1); print(json.dumps(rep))
