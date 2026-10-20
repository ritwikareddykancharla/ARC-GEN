def build_program(d4, palette):
    # The original closed-object motion is 'left', i.e. direction (dr, dc) = (0, -1).
    # Map this direction vector through the D4 transform: optionally mirror each row,
    # then rotate clockwise (d4 % 4) times. One clockwise turn sends (dr, dc) to (dc, -dr).
    dr, dc = 0, -1
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    header = (
        "BG = %d\n" % palette[4]
        + "FG = %d\n" % palette[1]
        + "CLOSED_COLOR = %d\n" % palette[2]
        + "OPEN_COLOR = %d\n" % palette[3]
        + "CLOSED_DIR = (%d, %d)\n" % (dr, dc)
    )
    body = '''
import numpy as np
from collections import deque


def _components(mask):
    H, W = mask.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def _is_open(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    c1 = max(c for _, c in cells)
    h = r1 - r0 + 3
    w = c1 - c0 + 3
    shape = np.zeros((h, w), dtype=bool)
    for r, c in cells:
        shape[r - r0 + 1, c - c0 + 1] = True
    # Orthogonal-convex hull: fill every row and column between its extreme cells until stable.
    hull = shape.copy()
    changed = True
    while changed:
        changed = False
        for y in range(h):
            xs = np.where(hull[y])[0]
            if len(xs) and not hull[y, xs[0]:xs[-1] + 1].all():
                hull[y, xs[0]:xs[-1] + 1] = True
                changed = True
        for x in range(w):
            ys = np.where(hull[:, x])[0]
            if len(ys) and not hull[ys[0]:ys[-1] + 1, x].all():
                hull[ys[0]:ys[-1] + 1, x] = True
                changed = True
    # Flood-fill the background that is reachable from outside the padded box.
    outside = np.zeros((h, w), dtype=bool)
    outside[0, 0] = True
    q = deque([(0, 0)])
    while q:
        y, x = q.popleft()
        for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + ddy, x + ddx
            if 0 <= ny < h and 0 <= nx < w and not shape[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    added = hull & ~shape
    return bool((added & outside).any())


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = np.full((H, W), BG, dtype=int)
    mask = g != BG
    for cells in _components(mask):
        if _is_open(cells):
            dy, dx = -CLOSED_DIR[0], -CLOSED_DIR[1]
            colour = OPEN_COLOR
        else:
            dy, dx = CLOSED_DIR
            colour = CLOSED_COLOR
        ys = [r for r, _ in cells]
        xs = [c for _, c in cells]
        sy = sx = 0
        if dx < 0:
            sx = -min(xs)
        elif dx > 0:
            sx = W - 1 - max(xs)
        if dy < 0:
            sy = -min(ys)
        elif dy > 0:
            sy = H - 1 - max(ys)
        for r, c in cells:
            out[r + sy, c + sx] = colour
    return out.tolist()
'''
    return header + body
