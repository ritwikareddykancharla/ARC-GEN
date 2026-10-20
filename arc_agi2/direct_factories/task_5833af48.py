def build_program(d4, palette):
    bg = int(palette[0])
    two = int(palette[2])
    eight = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
TWO = %d
EIGHT = %d

def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != BG and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and g[ny, nx] != BG and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    comps = _components(g)
    comps.sort(key=len, reverse=True)
    y0, x0, y1, x1 = _bbox(comps[0])
    C = int(g[y0, x0])
    H, W = y1 - y0 + 1, x1 - x0 + 1
    motif = None
    pattern = None
    for c in comps[1:]:
        a, b, cc, d = _bbox(c)
        sub = g[a:cc + 1, b:d + 1].copy()
        if motif is None and (sub == TWO).any():
            motif = sub
        elif pattern is None:
            pattern = sub
    out = np.full((H, W), C, dtype=int)
    if motif is None or pattern is None:
        return out.tolist()
    mh, mw = motif.shape
    bh, bw = max(1, H // mh), max(1, W // mw)
    fy = max(1, pattern.shape[0] // bh)
    fx = max(1, pattern.shape[1] // bw)
    small = pattern[::fy, ::fx][:bh, :bw]
    stamp = np.where(motif == TWO, C, motif)
    for by in range(min(bh, small.shape[0])):
        for bx in range(min(bw, small.shape[1])):
            if small[by, bx] == EIGHT:
                out[by * mh:(by + 1) * mh, bx * mw:(bx + 1) * mw] = stamp
    return out.tolist()
''' % (bg, two, eight)
    return src
