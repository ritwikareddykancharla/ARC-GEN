def build_program(d4, palette):
    bg_const = int(palette[0])
    src = '''
from collections import Counter, deque

BG = __BG__

def _components(g, h, w, bg):
    seen = [[False] * w for _ in range(h)]
    objs = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or g[y][x] == bg:
                continue
            col = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            q.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            objs.append((col, cells, (min(ys), min(xs), max(ys), max(xs))))
    return objs

def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    if h == 0 or w == 0:
        return g
    flat = [v for row in g for v in row]
    if BG in flat:
        bg = BG
    else:
        bg = Counter(flat).most_common(1)[0][0]
    objs = _components(g, h, w, bg)
    out = [row[:] for row in g]
    for col, cells, box in objs:
        n = len(cells)
        y0, x0, y1, x1 = box
        for ccol, ccells, cbox in objs:
            if ccol == col or len(ccells) <= n:
                continue
            a0, b0, a1, b1 = cbox
            if a0 <= y0 and y1 <= a1 and b0 <= x0 and x1 <= b1:
                for (y, x) in cells:
                    out[y][x] = bg
                break
    return out
'''
    return src.replace('__BG__', str(bg_const))
