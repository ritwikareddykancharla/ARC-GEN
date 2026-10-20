def build_program(d4, palette):
    one = int(palette[1])
    six = int(palette[6])
    # The mechanism is D4-equivariant in visible coordinates. Every D4 image of a
    # diagonal is again a diagonal (main and anti swap under odd rotations or a
    # reflection). The perpendicular of a diagonal direction (dy, dx) is
    # always (dy, -dx). So the visible-coordinate rule tests both diagonals
    # symmetrically and needs no axis specialisation from d4. Only the colour
    # roles are specialised from the palette.
    src = '''import numpy as np
from collections import Counter

ONE = __ONE__
SIX = __SIX__


def _background(g):
    return int(Counter(g.ravel().tolist()).most_common(1)[0][0])


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = _background(g)
    out = g.copy()
    ones = [(int(r), int(c)) for r, c in zip(*np.where(g == ONE))]
    sixes = set((int(r), int(c)) for r, c in zip(*np.where(g == SIX)))
    for i in range(len(ones)):
        for j in range(i + 1, len(ones)):
            (r0, c0), (r1, c1) = ones[i], ones[j]
            if r0 == r1 or abs(r1 - r0) != abs(c1 - c0):
                continue
            dr = 1 if r1 > r0 else -1
            dc = 1 if c1 > c0 else -1
            n = abs(r1 - r0)
            hits = []
            for k in range(1, n):
                r, c = r0 + k * dr, c0 + k * dc
                if (r, c) in sixes:
                    hits.append((r, c))
                elif out[r, c] == bg:
                    out[r, c] = ONE
            pr, pc = dr, -dc
            for sr, sc in hits:
                for sgn in (1, -1):
                    r, c = sr + sgn * pr, sc + sgn * pc
                    while 0 <= r < H and 0 <= c < W:
                        if out[r, c] == bg:
                            out[r, c] = SIX
                        r += sgn * pr
                        c += sgn * pc
    return out.tolist()
'''
    return src.replace('__ONE__', repr(one)).replace('__SIX__', repr(six))
