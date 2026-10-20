TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
BAR = __BAR__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
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
                comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    bars = []
    for comp in _components(g == BAR):
        ys = [c[0] for c in comp]
        xs = [c[1] for c in comp]
        bars.append((set(comp), min(ys), min(xs), max(ys), max(xs)))
    for patch in _components((g != BG) & (g != BAR)):
        best = -1
        best_score = 0
        for i, b in enumerate(bars):
            bset = b[0]
            score = 0
            for (y, x) in patch:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if (y + dy, x + dx) in bset:
                            score += 1
            if score > best_score:
                best_score = score
                best = i
        if best < 0:
            continue
        _, by0, bx0, by1, bx1 = bars[best]
        pys = [c[0] for c in patch]
        pxs = [c[1] for c in patch]
        py0, py1 = min(pys), max(pys)
        px0, px1 = min(pxs), max(pxs)
        pat = g[py0:py1 + 1, px0:px1 + 1].copy()
        ph, pw = pat.shape
        if by0 == by1 and bx1 > bx0:
            for y in range(py0, py1 + 1):
                for x in range(bx0, bx1 + 1):
                    out[y, x] = pat[y - py0, (x - px0) % pw]
        elif bx0 == bx1 and by1 > by0:
            for y in range(by0, by1 + 1):
                for x in range(px0, px1 + 1):
                    out[y, x] = pat[(y - py0) % ph, x - px0]
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    bar = int(palette[5])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__BAR__', str(bar))
