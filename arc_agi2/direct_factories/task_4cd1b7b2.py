def build_program(d4, palette):
    hole = int(palette[0])
    cols = [int(palette[i]) for i in (1, 2, 3, 4)]
    src = '''
import numpy as np

HOLE = %d
COLOURS = %r

def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    h = len(g)
    w = len(g[0]) if h else 0
    colours = list(COLOURS)
    if not (h == 4 and w == 4):
        seen = set()
        for r in g:
            for v in r:
                if v != HOLE:
                    seen.add(v)
        for d in demonstrations:
            for r in d['output']:
                for v in r:
                    if v != HOLE:
                        seen.add(v)
        colours = sorted(seen) if seen else colours
    cset = set(colours)

    def cands(y, x):
        used = set(g[y][c] for c in range(w) if g[y][c] != HOLE)
        used |= set(g[r][x] for r in range(h) if g[r][x] != HOLE)
        return cset - used

    # deduction passes: a line missing exactly one colour gets it
    changed = True
    while changed:
        changed = False
        for y in range(h):
            holes = [x for x in range(w) if g[y][x] == HOLE]
            if len(holes) == 1:
                miss = cset - set(g[y][x] for x in range(w) if g[y][x] != HOLE)
                if len(miss) == 1:
                    g[y][holes[0]] = next(iter(miss))
                    changed = True
        for x in range(w):
            holes = [y for y in range(h) if g[y][x] == HOLE]
            if len(holes) == 1:
                miss = cset - set(g[y][x] for y in range(h) if g[y][x] != HOLE)
                if len(miss) == 1:
                    g[holes[0]][x] = next(iter(miss))
                    changed = True
        for y in range(h):
            for x in range(w):
                if g[y][x] == HOLE:
                    c = cands(y, x)
                    if len(c) == 1:
                        g[y][x] = next(iter(c))
                        changed = True

    def bt():
        for y in range(h):
            for x in range(w):
                if g[y][x] == HOLE:
                    for v in sorted(cands(y, x)):
                        g[y][x] = v
                        if bt():
                            return True
                    g[y][x] = HOLE
                    return False
        return True

    if any(v == HOLE for r in g for v in r):
        snapshot = [r[:] for r in g]
        if not bt():
            g = snapshot
    return g
''' % (hole, cols)
    return src
