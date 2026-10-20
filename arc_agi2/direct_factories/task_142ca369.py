PROGRAM_TEMPLATE = '''
def solve(demonstrations, grid):
    BG = __BG__
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    # single-colour 4-connected components of non-background cells
    seen = [[False] * W for _ in range(H)]
    objs = []
    for y in range(H):
        for x in range(W):
            if g[y][x] != BG and not seen[y][x]:
                col = g[y][x]
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ddy, ddx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + ddy, cx + ddx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                objs.append((col, sorted(cells)))
    def box(cells):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        return min(ys), min(xs), max(ys), max(xs)
    emitters = []
    refl = [[False] * W for _ in range(H)]
    for col, cells in objs:
        y0, x0, y1, x1 = box(cells)
        if len(cells) == 3 and y1 - y0 == 1 and x1 - x0 == 1:
            emitters.append((col, cells, (y0, x0, y1, x1)))
        else:
            for cy, cx in cells:
                refl[cy][cx] = True
    src = [row[:] for row in g]
    emitters.sort(key=lambda e: (e[2][0], e[2][1]))
    for col, cells, (y0, x0, y1, x1) in emitters:
        cs = set(cells)
        missing = [(yy, xx) for yy in (y0, y1) for xx in (x0, x1) if (yy, xx) not in cs][0]
        tip = (y0 + y1 - missing[0], x0 + x1 - missing[1])
        dy = tip[0] - missing[0]
        dx = tip[1] - missing[1]
        c = col
        y, x = tip
        for _ in range(H + W):
            ny, nx = y + dy, x + dx
            if not (0 <= ny < H and 0 <= nx < W) or refl[ny][nx]:
                break
            for ay, ax, vert in ((ny - 1, nx, True), (ny + 1, nx, True), (ny, nx - 1, False), (ny, nx + 1, False)):
                if 0 <= ay < H and 0 <= ax < W and refl[ay][ax]:
                    c = src[ay][ax]
                    if vert:
                        dy = -dy
                    else:
                        dx = -dx
            g[ny][nx] = c
            y, x = ny, nx
    return g
'''


def build_program(d4, palette):
    bg = int(palette[0])
    return PROGRAM_TEMPLATE.replace('__BG__', str(bg))
