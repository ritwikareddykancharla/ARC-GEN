def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[1])
    src = '''import numpy as np

BG = %d
FILL = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    for s in range(min(H, W), 1, -1):
        # Collect every s x s window that is entirely background right now.
        cands = []
        for y in range(H - s + 1):
            for x in range(W - s + 1):
                if (g[y:y + s, x:x + s] == BG).all():
                    cands.append((y, x))
        # In the generator's domain, same-size holes never overlap, so the
        # stamping order does not matter. If two windows do overlap, a window
        # is stamped only if it is still entirely background when reached.
        for (y, x) in cands:
            if (g[y:y + s, x:x + s] == BG).all():
                g[y:y + s, x:x + s] = FILL
    return g.tolist()
''' % (bg, fill)
    return src
