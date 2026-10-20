def build_program(d4, palette):
    BG = int(palette[6])
    WALL = int(palette[9])
    FIVE = int(palette[5])
    SEVEN = int(palette[7])
    # Rotations keep handedness; reflections reverse it.
    # Canonical scan: the secondary sweep is the motion vector rotated clockwise.
    chir = 1 if int(d4) % 8 < 4 else -1
    header = (
        'import numpy as np\n'
        'from collections import deque\n'
        'BG = %d\n'
        'WALL = %d\n'
        'FIVE = %d\n'
        'SEVEN = %d\n'
        'CHIR = %d\n'
    ) % (BG, WALL, FIVE, SEVEN, chir)
    body = '''
def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
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
                    for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    mask = (g != BG) & (g != WALL)
    jobs = []
    for comp in _components(mask):
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        for dy, dx in ((0, 1), (0, -1), (-1, 0), (1, 0)):
            def line(k, dy=dy, dx=dx):
                if dx:
                    x = x1 + k if dx > 0 else x0 - k
                    if not 0 <= x < W:
                        return None
                    return g[y0:y1 + 1, x]
                y = y1 + k if dy > 0 else y0 - k
                if not 0 <= y < H:
                    return None
                return g[y, x0:x1 + 1]
            l1 = line(1)
            if l1 is None or not np.all(l1 == WALL):
                continue
            gap, k = 0, 2
            while True:
                l = line(k)
                if l is None or np.all(l == WALL):
                    break
                gap += 1
                k += 1
            box = g[y0:y1 + 1, x0:x1 + 1].copy()
            n5 = int(np.sum(box[1:-1, 1:-1] == FIVE)) if box.shape[0] > 2 and box.shape[1] > 2 else 0
            move = min(n5, gap + 1)
            jobs.append((y0, x0, y1, x1, box, dy, dx, move))
            break
    for y0, x0, y1, x1, box, dy, dx, move in jobs:
        if CHIR == 1:
            sy, sx = dx, -dy
        else:
            sy, sx = -dx, dy
        nb = box.copy()
        cells = [(r, c) for r in range(1, box.shape[0] - 1) for c in range(1, box.shape[1] - 1)]
        cells.sort(key=lambda p: (-(p[0] * dy + p[1] * dx), p[0] * sy + p[1] * sx))
        cnt = 0
        for r, c in cells:
            if cnt >= move:
                break
            if nb[r, c] == FIVE:
                nb[r, c] = SEVEN
                cnt += 1
        out[y0:y1 + 1, x0:x1 + 1] = BG
        if dx:
            wx = x1 + 1 if dx > 0 else x0 - 1
            out[y0:y1 + 1, wx] = BG
        else:
            wy = y1 + 1 if dy > 0 else y0 - 1
            out[wy, x0:x1 + 1] = BG
        ny0, nx0 = y0 + dy * move, x0 + dx * move
        ny1, nx1 = y1 + dy * move, x1 + dx * move
        if dx:
            wx = nx1 + 1 if dx > 0 else nx0 - 1
            out[ny0:ny1 + 1, wx] = WALL
        else:
            wy = ny1 + 1 if dy > 0 else ny0 - 1
            out[wy, nx0:nx1 + 1] = WALL
        out[ny0:ny1 + 1, nx0:nx1 + 1] = nb
    return out.tolist()
'''
    return header + body
