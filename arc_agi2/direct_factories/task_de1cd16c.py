PROGRAM = r'''
import numpy as np
from collections import Counter


def _segments(m, dot):
    # Split the rows of m into maximal bands of consecutive rows. Within a band
    # every column keeps one consistent non-dot colour. Dot cells act as wildcards.
    n, w = m.shape
    segs = []
    start = 0
    prof = np.full(w, -1, dtype=int)
    for i in range(n):
        row = m[i]
        known = row != dot
        conflict = bool(np.any(known & (prof != -1) & (row != prof)))
        if conflict:
            segs.append((start, i))
            start = i
            prof = np.full(w, -1, dtype=int)
        upd = known & (prof == -1)
        prof[upd] = row[upd]
    segs.append((start, n))
    return segs


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    vals, cnts = np.unique(g, return_counts=True)
    if len(vals) == 1:
        return [[int(vals[0])]]
    # The dot colour is the rarest colour in the grid.
    m = int(cnts.min())
    dot = int(min(int(v) for v, c in zip(vals, cnts) if c == m))
    # Recover the block-rectangle partition directly in the visible coordinates.
    rsegs = _segments(g, dot)
    csegs = _segments(g.T, dot)
    tally = {}
    for r0, r1 in rsegs:
        for c0, c1 in csegs:
            blk = g[r0:r1, c0:c1]
            nd = blk[blk != dot]
            if nd.size == 0:
                continue
            colour = Counter(nd.tolist()).most_common(1)[0][0]
            k = int((blk == dot).sum())
            tally[colour] = tally.get(colour, 0) + k
    if not tally:
        return [[dot]]
    best = max(tally.values())
    cands = [c for c, v in tally.items() if v == best]
    if len(cands) == 1:
        return [[int(cands[0])]]
    # A tie is out of the generator's domain, because quadrant counts are distinct.
    # Fall back to the candidate whose region is largest.
    area = {c: int((g == c).sum()) for c in cands}
    return [[int(max(cands, key=lambda c: (area[c], -c)))]]
'''


def build_program(d4, palette):
    # The mechanism is invariant under D4 and palette changes. Rows and columns are
    # segmented symmetrically, and the dot and region roles are read from the pixels.
    # So the same direct-coordinate program serves every variant.
    return PROGRAM
