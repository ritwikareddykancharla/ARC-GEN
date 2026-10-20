def build_program(d4, palette):
    d4 = int(d4) % 8
    # The original legend sits in the bottom-left corner.
    # Corner flags: (row_is_last, col_is_last).
    cr, cc = 1, 0
    # Bars stack upward from the corner.
    ur, uc = -1, 0
    # The paint colour sits one column to the right of the shape colour.
    pr, pc = 0, 1
    if d4 >= 4:
        # Reverse each row: columns mirror.
        cc = 1 - cc
        uc = -uc
        pc = -pc
    for _ in range(d4 % 4):
        # Clockwise rotation: (r, c) -> (c, h-1-r).
        cr, cc = cc, 1 - cr
        ur, uc = uc, -ur
        pr, pc = pc, -pr
    bg = int(palette[0])
    template = '''from collections import deque

BG = __BG__
CORNER_ROW_END = __CR__
CORNER_COL_END = __CC__
UP_DR = __UR__
UP_DC = __UC__
SIDE_DR = __PR__
SIDE_DC = __PC__


def _read_legend(g, H, W):
    r0 = CORNER_ROW_END * (H - 1)
    c0 = CORNER_COL_END * (W - 1)

    def cell(t, side):
        r = r0 + t * UP_DR + side * SIDE_DR
        c = c0 + t * UP_DC + side * SIDE_DC
        if 0 <= r < H and 0 <= c < W:
            return (r, c)
        return None

    legend = {}
    cells = set()
    i = 0
    while True:
        t = 3 * i
        if i > 0:
            gap = [cell(t - 1, 0), cell(t - 1, 1)]
            if any(p is None or g[p[0]][p[1]] != BG for p in gap):
                break
        pts = [cell(t, 0), cell(t, 1), cell(t + 1, 0), cell(t + 1, 1)]
        if any(p is None for p in pts):
            break
        vals = [g[p[0]][p[1]] for p in pts]
        a, b = vals[0], vals[1]
        if vals[2] != a or vals[3] != b or a == BG or b == BG or a == b:
            break
        used = set(legend) | set(legend.values())
        if a in used or b in used:
            break
        legend[a] = b
        cells.update(pts)
        i += 1
    return legend, cells


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    if H == 0 or W == 0:
        return out
    legend, lcells = _read_legend(g, H, W)
    if not legend:
        return out
    seen = [[False] * W for _ in range(H)]
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for r in range(H):
        for c in range(W):
            col = g[r][c]
            if seen[r][c] or col not in legend:
                continue
            comp = []
            q = deque([(r, c)])
            seen[r][c] = True
            while q:
                y, x = q.popleft()
                comp.append((y, x))
                for dy, dx in steps:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            if any(p in lcells for p in comp):
                continue
            paint = legend[col]
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            Y0 = max(0, min(ys) - 1)
            X0 = max(0, min(xs) - 1)
            Y1 = min(H - 1, max(ys) + 1)
            X1 = min(W - 1, max(xs) + 1)
            reach = set()
            stack = []
            for y in range(Y0, Y1 + 1):
                for x in range(X0, X1 + 1):
                    if (y in (Y0, Y1) or x in (X0, X1)) and g[y][x] == BG:
                        reach.add((y, x))
                        stack.append((y, x))
            while stack:
                y, x = stack.pop()
                for dy, dx in steps:
                    ny, nx = y + dy, x + dx
                    if Y0 <= ny <= Y1 and X0 <= nx <= X1 and (ny, nx) not in reach and g[ny][nx] == BG:
                        reach.add((ny, nx))
                        stack.append((ny, nx))
            for y, x in reach:
                out[y][x] = paint
    return out
'''
    src = (template.replace('__BG__', str(bg))
           .replace('__CR__', str(cr)).replace('__CC__', str(cc))
           .replace('__UR__', str(ur)).replace('__UC__', str(uc))
           .replace('__PR__', str(pr)).replace('__PC__', str(pc)))
    return src
