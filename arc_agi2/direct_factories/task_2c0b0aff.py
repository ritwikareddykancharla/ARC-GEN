def build_program(d4, palette):
    bg = int(palette[0])
    mark = int(palette[3])
    fill = int(palette[8])
    src = '''
from collections import deque

BG = %d
MARK = %d
FILL = %d

def _components(grid, pred):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if pred(grid[y][x]) and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and pred(grid[ny][nx]):
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out

def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)

def _count_plus(panel):
    n = 0
    for comp in _components(panel, lambda v: v == MARK):
        if len(comp) != 5:
            continue
        y0, x0, y1, x1 = _bbox(comp)
        cy, cx = y0 + 1, x0 + 1
        plus = {(cy, cx), (cy-1, cx), (cy+1, cx), (cy, cx-1), (cy, cx+1)}
        if y1 - y0 == 2 and x1 - x0 == 2 and set(comp) == plus:
            n += 1
    return n

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    best = None
    best_n = -1
    for comp in _components(g, lambda v: v != BG):
        y0, x0, y1, x1 = _bbox(comp)
        panel = [row[x0:x1 + 1] for row in g[y0:y1 + 1]]
        n = _count_plus(panel)
        if n > best_n:
            best_n = n
            best = panel
    if best is None:
        return [row[:] for row in g]
    return [row[:] for row in best]
''' % (bg, mark, fill)
    return src
