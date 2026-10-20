def build_program(d4, palette):
    bg = int(palette[0])
    frame = int(palette[2])
    fill = int(palette[3])
    src = '''
from collections import deque

BG = %d
FRAME = %d
FILL = %d

def _components(grid, h, w):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] != BG and not seen[y][x]:
                col = grid[y][x]
                q = deque([(y, x)])
                seen[y][x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and grid[ny][nx] == col:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [[BG] * w for _ in range(h)]
    for cells in _components(g, h, w):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if y1 - y0 < 2 or x1 - x0 < 2:
            continue
        for y in range(y0 + 1, y1):
            for x in range(x0 + 1, x1):
                if g[y][x] == BG:
                    out[y][x] = FILL
    return out
''' % (bg, frame, fill)
    return src
