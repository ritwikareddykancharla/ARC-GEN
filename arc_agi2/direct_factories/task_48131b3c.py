def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np

BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    cols = [int(c) for c in np.unique(g)]
    others = [c for c in cols if c != BG]
    if others:
        ink = others[0]
        if len(others) > 1 and BG not in cols:
            # Defensive: two colours present but neither is the background; swap them.
            a, b = others[0], others[1]
            inv = np.where(g == a, b, np.where(g == b, a, g))
            return np.tile(inv, (2, 2)).astype(int).tolist()
    else:
        # Degenerate: only background present. Borrow an ink colour from the demonstrations.
        ink = None
        for d in demonstrations:
            for key in ('input', 'output'):
                arr = np.array(d[key], dtype=int)
                cand = [int(c) for c in np.unique(arr) if int(c) != BG]
                if cand:
                    ink = cand[0]
                    break
            if ink is not None:
                break
        if ink is None:
            ink = BG
    # Swap the background and ink colours in every cell.
    inv = np.where(g == BG, ink, np.where(g == ink, BG, g))
    # A 2x2 tiling commutes with every D4 transform, so it is written directly in visible coordinates.
    out = np.tile(inv, (2, 2))
    return out.astype(int).tolist()
''' % bg
    return src
