def build_program(d4, palette):
    # Original motion: every object moves toward row 0 (away from the floor row),
    # i.e. direction vector (-1, 0). Transform it into visible coordinates.
    # Reflection (d4 >= 4) reverses each row, which negates the column component.
    # One clockwise rotation maps (r, c) -> (c, H-1-r), so a vector (dr, dc) becomes (dc, -dr).
    dr, dc = -1, 0
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    bg = int(palette[7])
    floor = int(palette[8])
    src = '''
BG = __BG__
FLOOR = __FLOOR__
DR = __DR__
DC = __DC__

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    objs = []
    for y in range(h):
        for x in range(w):
            col = g[y][x]
            if col == BG or col == FLOOR or seen[y][x]:
                continue
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            objs.append((col, cells))
    out = [row[:] for row in g]
    for col, cells in objs:
        for y, x in cells:
            out[y][x] = BG
    for col, cells in objs:
        s = len(cells)
        for y, x in cells:
            ny = y + DR * s
            nx = x + DC * s
            if 0 <= ny < h and 0 <= nx < w:
                out[ny][nx] = col
    return out
'''
    src = src.replace('__BG__', str(bg)).replace('__FLOOR__', str(floor))
    src = src.replace('__DR__', str(int(dr))).replace('__DC__', str(int(dc)))
    return src
