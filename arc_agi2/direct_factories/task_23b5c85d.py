def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    counts = {}
    for v in g.ravel().tolist():
        if v == BG:
            continue
        counts[v] = counts.get(v, 0) + 1
    if not counts:
        return [row[:] for row in np.asarray(grid).tolist()]
    best = None
    best_key = None
    for colour, n in counts.items():
        ys, xs = np.nonzero(g == colour)
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        area = (y1 - y0 + 1) * (x1 - x0 + 1)
        # Rarest colour first (constructor guarantees strict rarity);
        # tie-break by a fully solid bbox, then smaller bbox area.
        solid = 0 if area == n else 1
        key = (n, solid, area, colour)
        if best_key is None or key < best_key:
            best_key = key
            best = (colour, y0, y1, x0, x1)
    colour, y0, y1, x0, x1 = best
    h = y1 - y0 + 1
    w = x1 - x0 + 1
    return [[int(colour)] * w for _ in range(h)]
''' % bg
    return src
