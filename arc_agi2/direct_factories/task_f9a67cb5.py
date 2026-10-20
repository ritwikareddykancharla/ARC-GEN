def build_program(d4, palette):
    bg = int(palette[0])
    wall = int(palette[8])
    mark = int(palette[2])
    src = '''import numpy as np

BG = %d
WALL = %d
MARK = %d


def _flow_direction(g, my, mx):
    H, W = g.shape
    on_top = my == 0
    on_bot = my == H - 1
    on_left = mx == 0
    on_right = mx == W - 1
    # Unambiguous edge: flow goes inward, perpendicular to that edge.
    if on_top and not (on_left or on_right):
        return (1, 0)
    if on_bot and not (on_left or on_right):
        return (-1, 0)
    if on_left and not (on_top or on_bot):
        return (0, 1)
    if on_right and not (on_top or on_bot):
        return (0, -1)
    # Fallback (corner or interior marker): use the wall orientation.
    blocked = (g != BG) & (g != MARK)
    row_lines = int(np.sum(blocked.sum(axis=1) * 2 >= W)) if W > 0 else 0
    col_lines = int(np.sum(blocked.sum(axis=0) * 2 >= H)) if H > 0 else 0
    if row_lines >= col_lines:
        # walls are horizontal, flow is vertical
        return (1, 0) if my * 2 < H else (-1, 0)
    return (0, 1) if mx * 2 < W else (0, -1)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.where(g == MARK)
    if len(ys) == 0:
        return out.tolist()
    my, mx = int(ys[0]), int(xs[0])
    dy, dx = _flow_direction(g, my, mx)
    sides = [(dx, dy), (-dx, -dy)]

    def inb(y, x):
        return 0 <= y < H and 0 <= x < W

    def is_wall(y, x):
        v = int(g[y, x])
        return v == WALL or (v != BG and v != MARK)

    # Closure: every reached cell either flows forward (ahead is open),
    # or, if the cell ahead is a wall, spreads to both side neighbours.
    # A spreading cell whose ahead is open is a gap: it flows forward
    # and does not keep spreading, so each side stops at the first gap.
    seen = set()
    stack = [(my, mx)]
    while stack:
        y, x = stack.pop()
        if (y, x) in seen:
            continue
        seen.add((y, x))
        ay, ax = y + dy, x + dx
        if not inb(ay, ax):
            continue
        if is_wall(ay, ax):
            for sy, sx in sides:
                ny, nx = y + sy, x + sx
                if inb(ny, nx) and not is_wall(ny, nx) and (ny, nx) not in seen:
                    stack.append((ny, nx))
        else:
            if (ay, ax) not in seen:
                stack.append((ay, ax))
    for (y, x) in seen:
        out[y, x] = MARK
    return out.tolist()
''' % (bg, wall, mark)
    return src
