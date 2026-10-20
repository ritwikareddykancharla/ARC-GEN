PROGRAM = '''import numpy as np
from collections import Counter

DIAGS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _regions(g):
    cnt = Counter(int(v) for v in g.ravel())
    order = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    return [c for c, _ in order[:2]]


def _underlying(g, regions, seed):
    # Model the background as full-length stripes of colour S over a field of B.
    # A cell is S iff its row or its column is entirely S, ignoring seed pixels.
    best = None
    for S in regions:
        B = regions[1] if S == regions[0] else regions[0]
        isS = (g == S) | seed
        rowS = isS.all(axis=1)
        colS = isS.all(axis=0)
        pred = np.where(rowS[:, None] | colS[None, :], S, B)
        mism = int(((pred != g) & ~seed).sum())
        if best is None or mism < best[0]:
            best = (mism, pred)
    return best


def _neigh_major(g, regions, r, c):
    H, W = g.shape
    cnt = Counter()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < H and 0 <= cc < W and int(g[rr, cc]) in regions:
                cnt[int(g[rr, cc])] += 1
    if not cnt:
        return None
    return max(sorted(cnt), key=lambda k: cnt[k])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    regions = _regions(g)
    if len(regions) < 2:
        return g.tolist()
    seed = ~np.isin(g, regions)
    pts = [(int(r), int(c)) for r, c in zip(*np.nonzero(seed))]
    if not pts:
        return g.tolist()
    mism, pred = _underlying(g, regions, seed)
    votes = {}
    for r, c in pts:
        if mism == 0:
            u = int(pred[r, c])
        else:
            u = _neigh_major(g, regions, r, c)
        if u is None:
            continue
        votes.setdefault(u, Counter())[int(g[r, c])] += 1
    mapping = {u: cnt.most_common(1)[0][0] for u, cnt in votes.items()}
    out = g.copy()
    for r, c in pts:
        for dr, dc in DIAGS:
            rr, cc = r + dr, c + dc
            while 0 <= rr < H and 0 <= cc < W:
                if not seed[rr, cc]:
                    v = int(g[rr, cc])
                    if v in mapping:
                        out[rr, cc] = mapping[v]
                rr += dr
                cc += dc
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism uses four diagonal rays, full-row/full-column stripe
    # detection, and colour roles inferred from pixel counts. All of these are
    # closed under every D4 transform and every colour permutation. The emitted
    # program therefore works directly in visible coordinates and visible
    # colours, so no specialization is needed.
    return PROGRAM
