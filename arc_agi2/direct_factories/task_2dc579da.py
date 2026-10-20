def build_program(d4, palette):
    # The mechanism is D4- and palette-equivariant: a square grid is cut by a
    # full centre row and a full centre column, and the answer is the quadrant
    # holding the single odd pixel. Under any rotation or reflection, a quadrant
    # maps to a quadrant and its crop maps to the transformed crop. So the same
    # visible-coordinate program is valid for every d4. Colour roles (line,
    # background, dot) are inferred from pixels, so the palette needs no
    # constants.
    return '''
def _uniform_rows(g):
    return [y for y in range(len(g)) if len(set(g[y])) == 1]

def _uniform_cols(g):
    h = len(g)
    w = len(g[0])
    return [x for x in range(w) if len(set(g[y][x] for y in range(h))) == 1]

def _locate_dividers(g):
    h = len(g)
    w = len(g[0])
    r = h // 2
    c = w // 2
    row_ok = len(set(g[r])) == 1
    col_ok = len(set(g[y][c] for y in range(h))) == 1
    if row_ok and col_ok and g[r][0] == g[0][c]:
        return r, c
    # Fallback: look for a uniform row and a uniform column of the same colour
    # that cross. Prefer the pair closest to the centre.
    rows = _uniform_rows(g)
    cols = _uniform_cols(g)
    best = None
    for y in rows:
        for x in cols:
            if g[y][0] == g[0][x]:
                key = (abs(y - (h - 1) / 2.0) + abs(x - (w - 1) / 2.0), y, x)
                if best is None or key < best:
                    best = key
    if best is not None:
        return best[1], best[2]
    return r, c

def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    h = len(g)
    w = len(g[0])
    r, c = _locate_dividers(g)
    quads = [(0, r, 0, c), (0, r, c + 1, w), (r + 1, h, 0, c), (r + 1, h, c + 1, w)]
    quads = [q for q in quads if q[1] > q[0] and q[3] > q[2]]
    if not quads:
        return g
    counts = {}
    for (y0, y1, x0, x1) in quads:
        for y in range(y0, y1):
            for x in range(x0, x1):
                v = g[y][x]
                counts[v] = counts.get(v, 0) + 1
    bg = max(sorted(counts), key=lambda k: counts[k])
    best = None
    for (y0, y1, x0, x1) in quads:
        odd = 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                if g[y][x] != bg:
                    odd += 1
        if odd > 0 and (best is None or odd > best[0]):
            best = (odd, (y0, y1, x0, x1))
    y0, y1, x0, x1 = best[1] if best is not None else quads[0]
    return [g[y][x0:x1] for y in range(y0, y1)]
'''
