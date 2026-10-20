PROGRAM_TEMPLATE = '''import numpy as np
from collections import Counter

BG = __BG__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    # Lattice lines are full rows / full columns containing no background pixel.
    lrows = [y for y in range(H) if np.all(g[y, :] != BG)]
    lcols = [x for x in range(W) if np.all(g[:, x] != BG)]
    rset = set(lrows)
    cset = set(lcols)
    # Line colour: most common colour on line pixels that are NOT intersections.
    # Only intersections can carry special colours, so this cannot be confused
    # by a large special region.
    cnt = Counter()
    for y in lrows:
        for x in range(W):
            if x not in cset:
                cnt[int(g[y, x])] += 1
    for x in lcols:
        for y in range(H):
            if y not in rset:
                cnt[int(g[y, x])] += 1
    if not cnt:
        for v in g.flatten().tolist():
            if v != BG:
                cnt[int(v)] += 1
    if not cnt or len(lrows) < 2 or len(lcols) < 2:
        return [[BG] * 3 for _ in range(3)]
    line_col = cnt.most_common(1)[0][0]
    special = [(i, j) for i, y in enumerate(lrows) for j, x in enumerate(lcols)
               if int(g[y, x]) != line_col]
    if not special:
        return [[BG] * 3 for _ in range(3)]
    r0 = min(i for i, _ in special)
    r1 = max(i for i, _ in special)
    c0 = min(j for _, j in special)
    c1 = max(j for _, j in special)
    h = max(r1 - r0, 1)
    w = max(c1 - c0, 1)
    out = [[BG] * w for _ in range(h)]
    for a in range(h):
        for b in range(w):
            i = r0 + a
            j = c0 + b
            if i + 1 >= len(lrows) or j + 1 >= len(lcols):
                continue
            corners = [int(g[lrows[i], lcols[j]]), int(g[lrows[i], lcols[j + 1]]),
                       int(g[lrows[i + 1], lcols[j]]), int(g[lrows[i + 1], lcols[j + 1]])]
            if len(set(corners)) == 1 and corners[0] != line_col and corners[0] != BG:
                out[a][b] = corners[0]
    return out
'''


def build_program(d4, palette):
    bg = int(palette[0])
    return PROGRAM_TEMPLATE.replace('__BG__', str(bg))
