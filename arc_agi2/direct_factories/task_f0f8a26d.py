def build_program(d4, palette):
    bg = int(palette[7])
    src = '''
BG = %d

def _components(g, bg):
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] != bg and not seen[y][x]:
                col = g[y][x]
                stack = [(y, x)]
                seen[y][x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append((col, cells))
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    bg = BG
    present = set(v for row in g for v in row)
    if bg not in present and h and w:
        counts = {}
        for row in g:
            for v in row:
                counts[v] = counts.get(v, 0) + 1
        bg = max(counts, key=lambda k: counts[k])
    out = [[bg] * w for _ in range(h)]
    for col, cells in _components(g, bg):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        cy = (y0 + y1) // 2
        cx = (x0 + x1) // 2
        half = max(y1 - y0, x1 - x0) // 2
        vertical = (y1 - y0) > (x1 - x0)
        for d in range(-half, half + 1):
            if vertical:
                y, x = cy, cx + d
            else:
                y, x = cy + d, cx
            if 0 <= y < h and 0 <= x < w:
                out[y][x] = col
    return out
''' % bg
    return src
