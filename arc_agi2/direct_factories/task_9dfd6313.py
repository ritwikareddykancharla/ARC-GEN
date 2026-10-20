def build_program(d4, palette):
    k = d4 % 4
    flip = 1 if d4 >= 4 else 0
    # The gray (original colour 5) diagonal starts on the main diagonal.
    # A row reversal moves it to the anti-diagonal, and each clockwise
    # rotation swaps main and anti-diagonal, so the parity decides which
    # visible diagonal is the mirror line.
    anti = 1 if ((flip + k) % 2 == 1) else 0
    bg = int(palette[0])
    gray = int(palette[5])
    src = '''import numpy as np

ANTI = %d
BG = %d
GRAY = %d

def _mirror(r, c, n):
    # Reflection across the visible gray diagonal.
    if ANTI:
        return (n - 1 - c, n - 1 - r)
    return (c, r)

def _on_line(r, c, n):
    if ANTI:
        return r + c == n - 1
    return r == c

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    n = h
    if h != w:
        # The domain is always square; for safety, fall back to the smaller side.
        n = min(h, w)
    canvas = g.copy()
    # Stage 1: clear every coloured off-line piece.
    pieces = []
    for r in range(n):
        for c in range(n):
            if _on_line(r, c, n):
                continue
            v = int(g[r, c])
            if v != BG:
                pieces.append((r, c, v))
            canvas[r, c] = BG
    # Stage 2: redraw each piece at its mirror image across the gray line.
    for r, c, v in pieces:
        mr, mc = _mirror(r, c, n)
        canvas[mr, mc] = v
    return canvas.tolist()
''' % (anti, bg, gray)
    return src
