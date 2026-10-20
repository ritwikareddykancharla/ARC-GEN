def build_program(d4, palette):
    bg = int(palette[0])
    fr = int(palette[5])
    f1 = int(palette[6])
    f2 = int(palette[7])
    f3 = int(palette[8])
    src = '''import numpy as np
from collections import deque

BG = %d
FR = %d
FILL = {1: %d, 2: %d, 3: %d}


def _is_frame(g, y0, x0, L):
    h, w = g.shape
    if y0 < 0 or x0 < 0 or y0 + L > h or x0 + L > w:
        return False
    blk = g[y0:y0 + L, x0:x0 + L]
    if not (np.all(blk[0, :] == FR) and np.all(blk[-1, :] == FR) and np.all(blk[:, 0] == FR) and np.all(blk[:, -1] == FR)):
        return False
    return bool(np.all(blk[1:-1, 1:-1] == BG))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    seen = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if g[y, x] != FR or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == FR:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            H = y1 - y0 + 1
            W = x1 - x0 + 1
            if H == W and (H - 2) in FILL and len(cells) == 4 * (H - 1) and _is_frame(g, y0, x0, H):
                sub = out[y0 + 1:y1, x0 + 1:x1]
                sub[g[y0 + 1:y1, x0 + 1:x1] == BG] = FILL[H - 2]
                continue
            # Fallback: component is not a single clean frame (e.g. touching frames);
            # search for exact hollow square frames inside its bounding box.
            for L in (5, 4, 3):
                for ty in range(y0, y1 - L + 2):
                    for tx in range(x0, x1 - L + 2):
                        if _is_frame(g, ty, tx, L):
                            sub = out[ty + 1:ty + L - 1, tx + 1:tx + L - 1]
                            sub[g[ty + 1:ty + L - 1, tx + 1:tx + L - 1] == BG] = FILL[L - 2]
    return out.tolist()
''' % (bg, fr, f1, f2, f3)
    return src
