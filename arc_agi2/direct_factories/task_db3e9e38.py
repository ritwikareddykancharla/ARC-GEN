def build_program(d4, palette):
    k = d4 % 4
    # Canonical: the line hangs from the top edge and the stairs share its top end.
    # Clockwise rotation moves the anchor edge: k=0 top, k=1 right, k=2 bottom, k=3 left.
    # The row reversal for d4>=4 only mirrors the axis across the line.
    # The staircase is symmetric about the line, so that reversal changes nothing.
    vert = (k % 2 == 0)
    anchor_start = k in (0, 3)
    header = 'LINE = %d\nALT = %d\nVERT = %s\nANCHOR_START = %s\n' % (int(palette[7]), int(palette[8]), vert, anchor_start)
    body = '''
import numpy as np

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    pts = np.argwhere(g == LINE)
    if len(pts) == 0:
        return out.tolist()
    if VERT:
        perp = int(pts[0][1])
        along = pts[:, 0]
        perp_n = W
    else:
        perp = int(pts[0][0])
        along = pts[:, 1]
        perp_n = H
    lo = int(along.min())
    hi = int(along.max())
    L = hi - lo + 1
    for d in range(1, L):
        colour = LINE if d % 2 == 0 else ALT
        n = L - d
        a0 = lo if ANCHOR_START else hi - n + 1
        a1 = a0 + n
        for p in (perp - d, perp + d):
            if 0 <= p < perp_n:
                if VERT:
                    out[a0:a1, p] = colour
                else:
                    out[p, a0:a1] = colour
    return out.tolist()
'''
    return header + body
