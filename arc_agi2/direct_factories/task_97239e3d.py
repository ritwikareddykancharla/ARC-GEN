def build_program(d4, palette):
    bg = int(palette[0])
    ring = int(palette[8])
    header = 'BG = ' + str(bg) + '\nRING = ' + str(ring) + '\n'
    body = '''

def _phase(residues):
    for r in range(4):
        if r not in residues:
            return r
    return 0


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    ring_rows = set()
    ring_cols = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] == RING:
                ring_rows.add(y % 4)
                ring_cols.add(x % 4)
    py = _phase(ring_rows)
    px = _phase(ring_cols)

    def is_ring_cell(y, x):
        a = (y - py) % 4
        b = (x - px) % 4
        return a != 0 and b != 0 and not (a == 2 and b == 2)

    out = [row[:] for row in g]
    cells = {}
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if v != BG and v != RING:
                cells.setdefault(v, []).append((y, x))
                out[y][x] = RING if is_ring_cell(y, x) else BG

    rects = []
    for c, pts in cells.items():
        ys = [p[0] for p in pts]
        xs = [p[1] for p in pts]
        ymin, ymax, xmin, xmax = min(ys), max(ys), min(xs), max(xs)
        y0 = max(0, ymin - ((ymin - py) % 4))
        y1 = min(H - 1, ymax + ((py - ymax) % 4))
        x0 = max(0, xmin - ((xmin - px) % 4))
        x1 = min(W - 1, xmax + ((px - xmax) % 4))
        area = (y1 - y0 + 1) * (x1 - x0 + 1)
        rects.append((-area, c, y0, y1, x0, x1))
    rects.sort()

    for _, c, y0, y1, x0, x1 in rects:
        for x in range(x0, x1 + 1):
            out[y0][x] = c
            out[y1][x] = c
        for y in range(y0, y1 + 1):
            out[y][x0] = c
            out[y][x1] = c
    for _, c, y0, y1, x0, x1 in rects:
        for y in range(y0 + 1, y1):
            if (y - py) % 4 != 2:
                continue
            for x in range(x0 + 1, x1):
                if (x - px) % 4 == 2:
                    out[y][x] = c
    return out
'''
    return header + body
