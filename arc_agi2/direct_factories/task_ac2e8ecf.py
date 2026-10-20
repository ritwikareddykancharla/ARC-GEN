def build_program(d4, palette):
    d4 = int(d4)
    # Original frames move toward row 0, so their direction is (dy, dx) = (-1, 0).
    dy, dx = -1, 0
    # A horizontal flip (reverse each row) negates dx.
    if d4 >= 4:
        dx = -dx
    # A clockwise quarter turn maps the direction (dy, dx) to (dx, -dy).
    for _ in range(d4 % 4):
        dy, dx = dx, -dy
    bg = int(palette[0])
    template = '''import numpy as np
from collections import deque

BG = __BG__
FRAME_DY = __DY__
FRAME_DX = __DX__


def _objects(g):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    objs = []
    for y in range(H):
        for x in range(W):
            if g[y, x] == BG or seen[y, x]:
                continue
            col = int(g[y, x])
            q = deque([(y, x)])
            seen[y, x] = True
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            objs.append((col, cells, (min(ys), min(xs), max(ys), max(xs))))
    return objs


def _has_hole(o):
    col, cells, box = o
    y0, x0, y1, x1 = box
    h, w = y1 - y0 + 1, x1 - x0 + 1
    ink = np.zeros((h, w), dtype=bool)
    for y, x in cells:
        ink[y - y0, x - x0] = True
    seen = np.zeros((h, w), dtype=bool)
    stack = []
    for y in range(h):
        for x in range(w):
            if (y in (0, h - 1) or x in (0, w - 1)) and not ink[y, x]:
                seen[y, x] = True
                stack.append((y, x))
    while stack:
        y, x = stack.pop()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and not ink[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                stack.append((ny, nx))
    return bool((~ink & ~seen).any())


def _settle(objs, dy, dx, H, W, out):
    # Box-level gravity toward one visible edge.
    # Only objects in this group, whose perpendicular spans overlap, block each other.
    vertical = dx == 0
    step = dy if vertical else dx
    length = H if vertical else W

    def spans(box):
        y0, x0, y1, x1 = box
        if vertical:
            return (y0, y1), (x0, x1)
        return (x0, x1), (y0, y1)

    if step < 0:
        order = sorted(objs, key=lambda o: (spans(o[2])[0][0], spans(o[2])[1][0]))
    else:
        order = sorted(objs, key=lambda o: (-spans(o[2])[0][1], spans(o[2])[1][0]))
    placed = []
    for o in order:
        col, cells, box = o
        (a0, a1), (b0, b1) = spans(box)
        if step < 0:
            target = 0
            for p0, p1, q0, q1 in placed:
                if q0 <= b1 and b0 <= q1:
                    target = max(target, p1 + 1)
            shift = target - a0
        else:
            target = length - 1
            for p0, p1, q0, q1 in placed:
                if q0 <= b1 and b0 <= q1:
                    target = min(target, p0 - 1)
            shift = target - a1
        placed.append((a0 + shift, a1 + shift, b0, b1))
        for y, x in cells:
            if vertical:
                ny, nx = y + shift, x
            else:
                ny, nx = y, x + shift
            if 0 <= ny < H and 0 <= nx < W:
                out[ny, nx] = col


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    objs = _objects(g)
    frames = [o for o in objs if _has_hole(o)]
    crosses = [o for o in objs if not _has_hole(o)]
    out = np.full((H, W), BG, dtype=int)
    _settle(frames, FRAME_DY, FRAME_DX, H, W, out)
    _settle(crosses, -FRAME_DY, -FRAME_DX, H, W, out)
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__DY__', str(dy))
                    .replace('__DX__', str(dx)))
