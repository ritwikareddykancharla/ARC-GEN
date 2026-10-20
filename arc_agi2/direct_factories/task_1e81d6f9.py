def build_program(d4, palette):
    # The key (legend) cell is at original (1,1): the centre of the 3x3 pocket
    # in the top-left corner, walled by the colour-5 L-frame.
    # Track which visible corner it ends up in: (row measured from bottom?, col measured from right?).
    rend, cend = False, False
    if d4 >= 4:
        cend = not cend  # reverse each row
    for _ in range(d4 % 4):
        # clockwise rotation: new_row = old_col, new_col = H-1-old_row
        rend, cend = cend, (not rend)
    bg = int(palette[0])
    frame = int(palette[5])
    prog = '''import numpy as np

BG = %d
FRAME = %d
ROW_FROM_END = %s
COL_FROM_END = %s

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    kr = h - 2 if ROW_FROM_END else 1
    kc = w - 2 if COL_FROM_END else 1
    out = g.copy()
    if not (0 <= kr < h and 0 <= kc < w):
        return out.tolist()
    key = int(g[kr, kc])
    if key == BG or key == FRAME:
        return out.tolist()
    mask = (g == key)
    mask[kr, kc] = False
    out[mask] = BG
    return out.tolist()
''' % (bg, frame, repr(rend), repr(cend))
    return prog
