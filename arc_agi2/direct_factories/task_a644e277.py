def build_program(d4, palette):
    # The mechanism (find the lattice line colour, find the crossings left unpainted,
    # crop their inclusive bounding box) treats rows and columns the same way, and it
    # infers colour roles from pixels. A crop of a bounding box in visible coordinates
    # is the same under every D4 transform, so d4 and palette need no constants here.
    # Every step runs directly on the visible grid.
    program = '''
import numpy as np

def _line_structure(g, strict):
    H, W = g.shape
    best = None
    for c in sorted(set(int(v) for v in g.ravel().tolist())):
        if strict:
            tr = max(W - 2, W // 2 + 1)
            tc = max(H - 2, H // 2 + 1)
        else:
            tr = W / 2.0
            tc = H / 2.0
        rows = [y for y in range(H) if int(np.sum(g[y] == c)) >= tr and (strict or int(np.sum(g[y] == c)) > tr)]
        cols = [x for x in range(W) if int(np.sum(g[:, x] == c)) >= tc and (strict or int(np.sum(g[:, x] == c)) > tc)]
        if not rows or not cols:
            continue
        full = sum(int(np.sum(g[y] == c)) for y in rows) + sum(int(np.sum(g[:, x] == c)) for x in cols)
        key = (len(rows) + len(cols), full, -c)
        if best is None or key > best[0]:
            best = (key, c, rows, cols)
    return best

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # A lattice line is a full row or column of the line colour. The only exceptions
    # are the hole crossings, and a line holds at most two of them. A non-line row
    # always crosses at least two line columns, so it cannot be this uniform.
    found = _line_structure(g, True)
    if found is None:
        found = _line_structure(g, False)
    if found is None:
        return g.tolist()
    _, line, rows, cols = found
    holes = [(y, x) for y in rows for x in cols if g[y, x] != line]
    if not holes:
        return g.tolist()
    y0 = min(h[0] for h in holes)
    y1 = max(h[0] for h in holes)
    x0 = min(h[1] for h in holes)
    x1 = max(h[1] for h in holes)
    return g[y0:y1 + 1, x0:x1 + 1].tolist()
'''
    return program
