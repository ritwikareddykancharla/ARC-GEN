def build_program(d4, palette):
    k = d4 % 4
    # Original 'downward' direction (toward the base edge the bars stand on) is (+1, 0).
    # A horizontal flip (d4>=4) leaves vertical directions unchanged.
    # Each clockwise rotation maps down->left->up->right.
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    dr, dc = dirs[k]
    bar = int(palette[2])
    fill = int(palette[8])
    src = '''
from collections import deque

BAR = %d
FILL = %d
DR = %d
DC = %d

def _components(g, colour):
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == colour and not seen[y][x]:
                seen[y][x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == colour:
                            seen[ny][nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    for cells in _components(g, BAR):
        # order cells from the bar's free tip toward the edge it stands on
        cells.sort(key=lambda p: (p[0] * DR + p[1] * DC, p[0], p[1]))
        n = len(cells) // 2
        if n > 0:
            for y, x in cells[len(cells) - n:]:
                g[y][x] = FILL
    return g
''' % (bar, fill, dr, dc)
    return src
