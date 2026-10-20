_TEMPLATE = '''
BG = __BG__
WIRE = __WIRE__
DECO = __DECO__
BLOCK = __BLOCK__
PIPE = (WIRE, DECO, BLOCK)
PORT = (WIRE, DECO)
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
NB8 = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
SOLID = frozenset((a, b) for a in range(3) for b in range(3))
XPAT = frozenset([(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)])
DPAT = frozenset([(0, 1), (1, 0), (1, 2), (2, 1)])


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    special = (BG, WIRE, DECO, BLOCK)

    def inb(y, x):
        return 0 <= y < h and 0 <= x < w

    def pipe(y, x):
        return inb(y, x) and g[y][x] in PIPE

    # Markers: 8-connected single-colour components with a 3x3 bounding box.
    seen = [[False] * w for _ in range(h)]
    markers = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or g[y][x] in special:
                continue
            c = g[y][x]
            seen[y][x] = True
            comp = [(y, x)]
            i = 0
            while i < len(comp):
                cy, cx = comp[i]
                i += 1
                for dy, dx in NB8:
                    ny, nx = cy + dy, cx + dx
                    if inb(ny, nx) and not seen[ny][nx] and g[ny][nx] == c:
                        seen[ny][nx] = True
                        comp.append((ny, nx))
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            if y1 - y0 != 2 or x1 - x0 != 2:
                continue
            rel = frozenset((p[0] - y0, p[1] - x0) for p in comp)
            if rel == SOLID:
                kind = 'S'
            elif rel == XPAT:
                kind = 'X'
            elif rel == DPAT:
                kind = 'D'
            else:
                continue
            markers.append((y0 + 1, x0 + 1, c, kind))

    # Occluding blocks: 4-connected components and their wire ports.
    owner = {}
    ports = []
    for y in range(h):
        for x in range(w):
            if g[y][x] != BLOCK or (y, x) in owner:
                continue
            idx = len(ports)
            owner[(y, x)] = idx
            comp = [(y, x)]
            i = 0
            while i < len(comp):
                cy, cx = comp[i]
                i += 1
                for dy, dx in DIRS:
                    ny, nx = cy + dy, cx + dx
                    if inb(ny, nx) and g[ny][nx] == BLOCK and (ny, nx) not in owner:
                        owner[(ny, nx)] = idx
                        comp.append((ny, nx))
            plist = []
            for cy, cx in comp:
                for dy, dx in DIRS:
                    ny, nx = cy + dy, cx + dx
                    if inb(ny, nx) and g[ny][nx] in PORT:
                        plist.append((ny, nx, dy, dx))
            ports.append(plist)

    def trace(cy, cx):
        starts = [d for d in DIRS if inb(cy + 2 * d[0], cx + 2 * d[1]) and
                  g[cy + 2 * d[0]][cx + 2 * d[1]] == WIRE]
        if len(starts) != 1:
            return None
        d = starts[0]
        y, x = cy + 2 * d[0], cx + 2 * d[1]
        for _ in range(4 * h * w + 16):
            ny, nx = y + d[0], x + d[1]
            if inb(ny, nx) and g[ny][nx] == BLOCK:
                exits = [p for p in ports[owner[(ny, nx)]] if (p[0], p[1]) != (y, x)]
                straight = [p for p in exits if (p[2], p[3]) == d and
                            (p[0] - y) * d[1] == (p[1] - x) * d[0]]
                if len(straight) == 1:
                    p = straight[0]
                elif not straight and len(exits) == 1:
                    p = exits[0]
                else:
                    return None
                y, x, d = p[0], p[1], (p[2], p[3])
                continue
            if pipe(ny, nx):
                y, x = ny, nx
                continue
            turns = [t for t in ((d[1], d[0]), (-d[1], -d[0])) if pipe(y + t[0], x + t[1])]
            if not turns:
                return (y + 2 * d[0], x + 2 * d[1])
            if len(turns) > 1:
                return None
            d = turns[0]
            y, x = y + d[0], x + d[1]
        return None

    out = [row[:] for row in g]

    def stamp(cy, cx, c, pat):
        for yy in range(cy - 1, cy + 2):
            for xx in range(cx - 1, cx + 2):
                if inb(yy, xx):
                    out[yy][xx] = BG
        for a, b in pat:
            yy, xx = cy - 1 + a, cx - 1 + b
            if inb(yy, xx):
                out[yy][xx] = c

    centres = set((m[0], m[1]) for m in markers)
    for cy, cx, c, kind in markers:
        end = trace(cy, cx)
        if end is None or end in centres:
            continue
        ey, ex = end
        if kind == 'S':
            stamp(cy, cx, c, DPAT)
            stamp(ey, ex, c, XPAT)
        elif kind == 'X':
            stamp(ey, ex, c, DPAT)
        else:
            stamp(ey, ex, c, XPAT)
    return out
'''


def build_program(d4, palette):
    def col(c):
        return int(palette[c])
    src = _TEMPLATE
    for name, c in (('__BG__', 0), ('__WIRE__', 8), ('__DECO__', 5), ('__BLOCK__', 9)):
        src = src.replace(name, str(col(c)))
    return src
