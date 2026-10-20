def build_program(d4, palette):
    d4 = int(d4) % 8
    quarter_turns = d4 % 4
    # A quarter turn maps up-down mirror symmetry to left-right mirror symmetry
    # and back. A row reversal keeps both of them. Diagonal symmetry (main or
    # anti) stays diagonal under every D4 element.
    swap = quarter_turns in (1, 3)
    col_ud = int(palette[3]) if swap else int(palette[1])
    col_lr = int(palette[1]) if swap else int(palette[3])
    col_d = int(palette[6])
    template = '''
COL_UD = __COL_UD__
COL_LR = __COL_LR__
COL_D = __COL_D__


def _background(grid):
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    best = None
    for c in sorted(counts):
        if best is None or counts[c] > counts[best]:
            best = c
    return best


def _components(grid, bg):
    h = len(grid)
    w = len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] == bg or seen[y][x]:
                continue
            colour = grid[y][x]
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and grid[ny][nx] == colour:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            comps.append(cells)
    return comps


def _mask(cells):
    y0 = min(c[0] for c in cells)
    x0 = min(c[1] for c in cells)
    y1 = max(c[0] for c in cells)
    x1 = max(c[1] for c in cells)
    m = [[0] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
    for y, x in cells:
        m[y - y0][x - x0] = 1
    return m


def _is_ud(m):
    return m == m[::-1]


def _is_lr(m):
    return all(row == row[::-1] for row in m)


def _is_diag(m):
    n = len(m)
    if n != len(m[0]):
        return False
    main = all(m[i][j] == m[j][i] for i in range(n) for j in range(n))
    anti = all(m[i][j] == m[n - 1 - j][n - 1 - i] for i in range(n) for j in range(n))
    return main or anti


def solve(demonstrations, grid):
    grid = [list(row) for row in grid]
    bg = _background(grid)
    out = [list(row) for row in grid]
    for cells in _components(grid, bg):
        if len(cells) == 1:
            y, x = cells[0]
            out[y][x] = bg
            continue
        m = _mask(cells)
        ud = _is_ud(m)
        lr = _is_lr(m)
        new = None
        if ud and not lr:
            new = COL_UD
        elif lr and not ud:
            new = COL_LR
        elif not ud and not lr and _is_diag(m):
            new = COL_D
        if new is None:
            continue
        for y, x in cells:
            out[y][x] = new
    return out
'''
    return (template.replace('__COL_UD__', str(col_ud))
                    .replace('__COL_LR__', str(col_lr))
                    .replace('__COL_D__', str(col_d)))
