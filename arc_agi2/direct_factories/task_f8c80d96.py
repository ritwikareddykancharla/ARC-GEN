def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[5])
    src = '''import numpy as np
from collections import Counter

BG = __BG__
FILL = __FILL__


def _ring_index(H, W, cy, cx):
    ys = np.arange(H)[:, None]
    xs = np.arange(W)[None, :]
    dy = np.ceil(np.abs(ys - cy) - 1e-09).astype(int)
    dx = np.ceil(np.abs(xs - cx) - 1e-09).astype(int)
    return np.maximum(dy, dx)


def _candidates(mask, H, W):
    found = []
    for ky in range(-2, 2 * H + 1):
        cy = ky / 2.0
        for kx in range(-2, 2 * W + 1):
            cx = kx / 2.0
            d = _ring_index(H, W, cy, cx)
            levels = sorted(set(d[mask].tolist()))
            if len(levels) < 2:
                continue
            if not np.array_equal(np.isin(d, levels), mask):
                continue
            steps = set(levels[i + 1] - levels[i] for i in range(len(levels) - 1))
            if len(steps) != 1:
                continue
            p = steps.pop()
            if p < 2:
                continue
            found.append((d, levels, p))
    return found


def _render(d, levels, p, col, shape):
    out = np.full(shape, FILL, dtype=int)
    r = levels[0] % p
    out[(d % p) == r] = col
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mask = g != BG
    if not mask.any():
        return np.full((H, W), FILL, dtype=int).tolist()
    col = Counter(g[mask].tolist()).most_common(1)[0][0]
    cands = _candidates(mask, H, W)
    if not cands:
        out = g.copy()
        out[~mask] = FILL
        return out.tolist()
    # Innermost visible frame is the first ring around the centre: level p-1.
    preferred = [c for c in cands if c[1][0] == c[2] - 1]
    pool = preferred if preferred else cands
    groups = {}
    order = []
    for d, levels, p in pool:
        out = _render(d, levels, p, col, (H, W))
        key = out.tobytes()
        if key not in groups:
            groups[key] = [out, 0, p]
            order.append(key)
        groups[key][1] += 1
    best = None
    for key in order:
        out, cnt, p = groups[key]
        score = (cnt, -p)
        if best is None or score > best[0]:
            best = (score, out)
    return best[1].tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__FILL__', str(fill))
