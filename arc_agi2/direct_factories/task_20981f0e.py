def build_program(d4, palette):
    bg = int(palette[0])
    shape = int(palette[1])
    mark = int(palette[2])
    src = '''import numpy as np

BG = %d
SHAPE = %d
MARK = %d


def _lattice(coords):
    vals = sorted(set(int(v) for v in coords))
    if len(vals) >= 2:
        diffs = [b - a for a, b in zip(vals, vals[1:]) if b - a > 0]
        period = min(diffs) if diffs else 5
    else:
        period = 5
    origin = vals[0] if vals else 0
    return origin, period


def _target(lo_edge, period, extent):
    gap = period - 1
    return lo_edge + 1 + (gap - extent) // 2


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    mr, mc = np.where(g == MARK)
    if len(mr) == 0:
        return g.tolist()
    r0, pr = _lattice(mr.tolist())
    c0, pc = _lattice(mc.tolist())
    out = g.copy()
    out[g == SHAPE] = BG
    groups = {}
    sr, sc = np.where(g == SHAPE)
    for y, x in zip(sr.tolist(), sc.tolist()):
        kr = (y - r0) // pr
        kc = (x - c0) // pc
        groups.setdefault((kr, kc), []).append((y, x))
    for (kr, kc), cells in groups.items():
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1 = min(ys), max(ys)
        x0, x1 = min(xs), max(xs)
        ty = _target(r0 + kr * pr, pr, y1 - y0 + 1)
        tx = _target(c0 + kc * pc, pc, x1 - x0 + 1)
        for y, x in cells:
            ny, nx = y - y0 + ty, x - x0 + tx
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = SHAPE
    return out.tolist()
''' % (bg, shape, mark)
    return src
