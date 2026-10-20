def build_program(d4, palette):
    bg = int(palette[7])
    # In the original frame, column lines (from vertical dominoes) are painted first
    # and row lines (from horizontal dominoes) on top. A reflection does not change
    # orientation. An odd number of clockwise quarter turns swaps rows and columns.
    # So in visible coordinates rows win for d4%4 in {0,2} and columns win otherwise.
    rows_on_top = (d4 % 4) in (0, 2)
    src = '''
BG = %d
ROWS_ON_TOP = %s

def _components(g, h, w):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or g[y][x] == BG:
                continue
            c = g[y][x]
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            comps.append((c, cells))
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [[BG] * w for _ in range(h)]
    col_lines = []
    row_lines = []
    for c, cells in _components(g, h, w):
        ys = set(p[0] for p in cells)
        xs = set(p[1] for p in cells)
        if len(cells) < 2:
            continue
        if len(xs) == 1 and len(ys) > 1:
            col_lines.append((next(iter(xs)), c))
        elif len(ys) == 1 and len(xs) > 1:
            row_lines.append((next(iter(ys)), c))
    def paint_cols():
        for x, c in col_lines:
            for y in range(h):
                out[y][x] = c
    def paint_rows():
        for y, c in row_lines:
            for x in range(w):
                out[y][x] = c
    if ROWS_ON_TOP:
        paint_cols()
        paint_rows()
    else:
        paint_rows()
        paint_cols()
    return out
''' % (bg, 'True' if rows_on_top else 'False')
    return src
