def build_program(d4, palette):
    bg = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    mask = g != BG
    seen = np.zeros((h, w), dtype=bool)
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0, x0] or seen[y0, x0]:
                continue
            comp = []
            q = deque([(y0, x0)])
            seen[y0, x0] = True
            while q:
                cy, cx = q.popleft()
                comp.append((cy, cx))
                for dy, dx in steps:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            s = set(comp)
            def nbrs(c):
                y, x = c
                return [p for p in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if p in s]
            ends = sorted(c for c in comp if len(nbrs(c)) <= 1)
            start = ends[0] if ends else sorted(comp)[0]
            path = [start]
            visited = {start}
            cur = start
            while True:
                nxt = [p for p in nbrs(cur) if p not in visited]
                if not nxt:
                    break
                cur = sorted(nxt)[0]
                visited.add(cur)
                path.append(cur)
            cols = [int(g[y, x]) for (y, x) in path]
            for (y, x), c in zip(path, cols[::-1]):
                out[y, x] = c
    return out.tolist()
''' % bg
    return src
