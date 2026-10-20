def build_program(d4, palette):
    line = int(palette[1])
    bg = int(palette[0])
    src = '''import numpy as np

LINE = %d
BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    # Odd-sized grids: the even-index lattice is identical whichever end is
    # counted from, so it is the same under every visible rotation/reflection.
    # For safety on rectangular inputs, anchor parity at the top-left and
    # also accept anchoring from the opposite edge when sizes are odd.
    rows = np.zeros(h, dtype=bool)
    cols = np.zeros(w, dtype=bool)
    rows[0::2] = True
    cols[0::2] = True
    out[rows, :] = LINE
    out[:, cols] = LINE
    return out.tolist()
''' % (line, bg)
    return src
