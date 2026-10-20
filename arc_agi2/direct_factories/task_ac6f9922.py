PROGRAM = '''import numpy as np
from collections import Counter, deque


def _comps(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
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
    h, w = g.shape
    # Background: the frame never touches the grid border, so the border is pure background.
    border = list(g[0, :]) + list(g[-1, :]) + list(g[:, 0]) + list(g[:, -1])
    bg = int(Counter(int(v) for v in border).most_common(1)[0][0])
    # Frame: the largest single-colour 4-connected non-background object.
    best = None
    for c in sorted(set(int(v) for v in g.ravel()) - {bg}):
        for cells in _comps(g == c):
            if best is None or len(cells) > len(best[1]):
                best = (c, cells)
    if best is None:
        return [[bg]]
    fc, cells = best
    ys = [p[0] for p in cells]
    xs = [p[1] for p in cells]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    sub = g[y0:y1 + 1, x0:x1 + 1]
    # Holes: connected regions of non-frame cells inside the frame box.
    infos = []
    for hc in _comps(sub != fc):
        hy = min(p[0] for p in hc)
        hx = min(p[1] for p in hc)
        col = bg
        for (y, x) in sorted(hc):
            if sub[y, x] != bg:
                col = int(sub[y, x])
                break
        infos.append((hy, hx, col))
    if not infos:
        return [[bg]]
    # Visible lattice: distinct hole tops give output rows, distinct hole lefts give output columns.
    rows = sorted(set(i[0] for i in infos))
    cols = sorted(set(i[1] for i in infos))
    out = [[bg] * len(cols) for _ in rows]
    for hy, hx, col in infos:
        out[rows.index(hy)][cols.index(hx)] = col
    return out
'''


def build_program(d4, palette):
    header = '# specialised for d4=%d palette=%s; the hole lattice is read directly in visible coordinates, and colour roles are inferred from pixels\n' % (int(d4), [int(p) for p in palette])
    return header + PROGRAM
