TEMPLATE = '''import numpy as np
from collections import Counter, deque

BG = __BG__

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    for sy in range(h):
        for sx in range(w):
            if g[sy, sx] == BG or seen[sy, sx]:
                continue
            q = deque([(sy, sx)])
            seen[sy, sx] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] != BG:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            iy0, iy1, ix0, ix1 = y0 + 1, y1 - 1, x0 + 1, x1 - 1
            if iy0 > iy1 or ix0 > ix1:
                continue
            cnt = Counter(int(g[y, x]) for y, x in cells)
            main = cnt.most_common(1)[0][0]
            others = [(n, c) for c, n in cnt.items() if c != main]
            if others:
                others.sort(key=lambda t: (-t[0], t[1]))
                marker = others[0][1]
            else:
                inner = g[iy0:iy1 + 1, ix0:ix1 + 1]
                if np.any(inner == BG):
                    marker = BG
                else:
                    continue
            maxdy = (iy1 - iy0) // 2
            maxdx = (ix1 - ix0) // 2
            for y in range(iy0, iy1 + 1):
                for x in range(ix0, ix1 + 1):
                    dy = min(y - iy0, iy1 - y)
                    dx = min(x - ix0, ix1 - x)
                    on = (dy == dx) or (dy == maxdy and dx >= dy) or (dx == maxdx and dy >= dx)
                    out[y, x] = marker if on else BG
    return out.tolist()
'''

def build_program(d4, palette):
    bg = int(palette[0])
    return TEMPLATE.replace('__BG__', str(bg))
