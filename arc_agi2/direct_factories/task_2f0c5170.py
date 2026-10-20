def build_program(d4, palette):
    bg = int(palette[8])
    box = int(palette[0])
    sprite = int(palette[4])
    src = '''import numpy as np
from collections import deque

BG = %d
BOX = %d
SPRITE = %d

def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    comps = [c for c in _components(g != BG) if len(c) > 1]
    if len(comps) < 2:
        comps = _components(g != BG)
    def key(c):
        nonbox = sum(1 for y, x in c if g[y, x] != BOX)
        spr = sum(1 for y, x in c if g[y, x] == SPRITE)
        return (-spr, -nonbox)
    comps.sort(key=key)
    tmpl, dst = comps[0], comps[1]
    ys = [p[0] for p in dst]
    xs = [p[1] for p in dst]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    marks = [(y, x) for y in range(out.shape[0]) for x in range(out.shape[1]) if out[y, x] != BOX]
    if not marks:
        return out.tolist()
    my, mx = marks[0]
    mcol = out[my, mx]
    srcm = [(y, x) for y, x in sorted(tmpl) if g[y, x] == mcol]
    if not srcm:
        return out.tolist()
    sy, sx = srcm[0]
    H, W = out.shape
    for y, x in tmpl:
        v = g[y, x]
        if v == BOX:
            continue
        ty, tx = my + (y - sy), mx + (x - sx)
        if 0 <= ty < H and 0 <= tx < W:
            out[ty, tx] = v
    return out.tolist()
''' % (bg, box, sprite)
    return src
