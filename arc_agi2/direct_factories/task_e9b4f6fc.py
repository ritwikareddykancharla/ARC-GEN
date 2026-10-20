TEMPLATE = '''BG = @BG@
DY = @DY@
DX = @DX@


def _components(g):
    h = len(g)
    w = len(g[0]) if h else 0
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y][x] == BG or seen[y][x]:
                continue
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] != BG:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    comps = _components(g)
    if not comps:
        return [row[:] for row in g]
    main = max(comps, key=len)
    ys = [c[0] for c in main]
    xs = [c[1] for c in main]
    y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
    crop = [row[x0:x1 + 1] for row in g[y0:y1 + 1]]
    mapping = {}
    for comp in comps:
        if comp is main or len(comp) != 2:
            continue
        (ay, ax), (by, bx) = comp
        if (by - ay, bx - ax) == (DY, DX):
            new, old = g[ay][ax], g[by][bx]
        elif (ay - by, ax - bx) == (DY, DX):
            new, old = g[by][bx], g[ay][ax]
        else:
            continue
        mapping[old] = new
    return [[mapping.get(v, v) for v in row] for row in crop]
'''


def build_program(d4, palette):
    k = d4 % 4
    v = (0, 1) if d4 < 4 else (0, -1)
    for _ in range(k):
        v = (v[1], -v[0])
    bg = int(palette[0])
    src = TEMPLATE.replace('@BG@', str(bg))
    src = src.replace('@DY@', str(int(v[0])))
    src = src.replace('@DX@', str(int(v[1])))
    return src
