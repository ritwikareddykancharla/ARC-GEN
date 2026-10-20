def build_program(d4, palette):
    bg = int(palette[0])
    big = int(palette[1])
    small = int(palette[8])
    src = '''
BG = %d
BIG = %d
SMALL = %d

def _pockets(g, h, w):
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == BG and not seen[y][x]:
                seen[y][x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == BG:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    out = [row[:] for row in g]
    comps = _pockets(g, h, w)
    if not comps:
        return out
    sizes = [len(c) for c in comps]
    mx = max(sizes)
    mn = min(sizes)
    for c in comps:
        if len(c) == mx:
            for y, x in c:
                out[y][x] = BIG
    for c in comps:
        if len(c) == mn:
            for y, x in c:
                out[y][x] = SMALL
    return out
''' % (bg, big, small)
    return src
