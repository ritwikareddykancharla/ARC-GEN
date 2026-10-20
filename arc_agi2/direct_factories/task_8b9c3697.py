TEMPLATE = '''import numpy as np
from collections import Counter, deque

RED = __RED__
TRAIL = __TRAIL__
DIRS = __DIRS__


def _components(mask):
    H, W = mask.shape
    seen = np.zeros((H, W), dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    shape_mask = np.zeros((H, W), dtype=bool)
    sid = -np.ones((H, W), dtype=int)
    boxes = []
    for colour in sorted(set(g.ravel().tolist()) - {bg, RED}):
        for cells in _components(g == colour):
            i = len(boxes)
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            boxes.append((min(ys), min(xs), max(ys), max(xs)))
            for y, x in cells:
                shape_mask[y, x] = True
                sid[y, x] = i
    out = g.copy()
    out[g == RED] = bg
    pieces = _components(g == RED) if RED != bg else []

    def inside(y, x):
        return 0 <= y < H and 0 <= x < W

    for cells in pieces:
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, x0, y1, x1 = min(ys), min(xs), max(ys), max(xs)
        if len(cells) != (y1 - y0 + 1) * (x1 - x0 + 1):
            continue
        for dy, dx in DIRS:
            k = 0
            ok = True
            while True:
                nxt = [(y + dy * (k + 1), x + dx * (k + 1)) for y, x in cells]
                if any(not inside(y, x) for y, x in nxt):
                    ok = False
                    break
                if any(shape_mask[y, x] for y, x in nxt):
                    break
                k += 1
            if not ok or k == 0:
                continue
            final = [(y + dy * k, x + dx * k) for y, x in cells]
            if dy:
                fy = (y0 if dy < 0 else y1) + dy * (k + 1)
                front = [(fy, x) for x in range(x0, x1 + 1)]
                ends = [(fy, x0 - 1), (fy, x1 + 1)]
            else:
                fx = (x0 if dx < 0 else x1) + dx * (k + 1)
                front = [(y, fx) for y in range(y0, y1 + 1)]
                ends = [(y0 - 1, fx), (y1 + 1, fx)]
            if not all(inside(y, x) and shape_mask[y, x] for y, x in front):
                continue
            ids = set(int(sid[y, x]) for y, x in front)
            if len(ids) != 1:
                continue
            if any(inside(y, x) and shape_mask[y, x] for y, x in ends):
                continue
            sb = boxes[ids.pop()]
            if not all(sb[0] <= y <= sb[2] and sb[1] <= x <= sb[3] for y, x in final):
                continue
            for s in range(k + 1):
                for y, x in cells:
                    out[y + dy * s, x + dx * s] = TRAIL
            for y, x in final:
                out[y, x] = RED
            break
    return out.tolist()
'''


def build_program(d4, palette):
    red = int(palette[2])
    trail = int(palette[0])
    dirs = []
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        if d4 >= 4:
            dx = -dx
        for _ in range(d4 % 4):
            dy, dx = dx, -dy
        dirs.append((dy, dx))
    src = TEMPLATE.replace('__RED__', str(red))
    src = src.replace('__TRAIL__', str(trail))
    src = src.replace('__DIRS__', repr(dirs))
    return src
