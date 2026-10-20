TEMPLATE = '''import numpy as np
from itertools import combinations

BG = __BG__
ARM = __ARM__
DOM_VERTICAL = __DOMV__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def arms(y, x):
        return [(y + dy, x + dx) for dy, dx in dirs]

    def is_centre(y, x):
        if g[y, x] == ARM:
            return False
        for yy, xx in arms(y, x):
            if not (0 <= yy < H and 0 <= xx < W) or g[yy, xx] != ARM:
                return False
        return True

    coloured = []
    hollow = []
    for y in range(H):
        for x in range(W):
            if is_centre(y, x):
                if g[y, x] == BG:
                    hollow.append((y, x))
                else:
                    coloured.append((y, x, int(g[y, x])))

    # Coloured centres are always genuine pluses. Background-centred
    # candidates may be genuine hollow pluses or pockets enclosed by the arms
    # of neighbouring pluses; keep a minimal set that explains all arm cells.
    covered = set()
    for y, x, _ in coloured:
        covered.update(arms(y, x))
    need = set()
    for y, x in hollow:
        for a in arms(y, x):
            if a not in covered:
                need.add(a)
    chosen = []
    remaining = list(hollow)
    changed = True
    while changed and need:
        changed = False
        for cand in list(remaining):
            ca = set(arms(*cand)) & need
            if not ca:
                continue
            others = set()
            for o in remaining:
                if o != cand:
                    others.update(arms(*o))
            if ca - others:
                chosen.append(cand)
                remaining.remove(cand)
                need -= set(arms(*cand))
                changed = True
    if need:
        pool = [c for c in remaining if set(arms(*c)) & need]
        best = None
        if len(pool) <= 14:
            for k in range(1, len(pool) + 1):
                for combo in combinations(pool, k):
                    cov = set()
                    for c in combo:
                        cov.update(arms(*c))
                    if need <= cov:
                        best = list(combo)
                        break
                if best is not None:
                    break
        if best is None:
            best = []
            left = set(need)
            while left and pool:
                c = max(pool, key=lambda p: len(set(arms(*p)) & left))
                gain = set(arms(*c)) & left
                if not gain:
                    break
                best.append(c)
                pool.remove(c)
                left -= gain
        chosen.extend(best)

    centres = list(coloured) + [(y, x, BG) for y, x in chosen]

    if DOM_VERTICAL:
        minor = ((0, 1), (0, -1))
        major = ((1, 0), (-1, 0))
    else:
        minor = ((1, 0), (-1, 0))
        major = ((0, 1), (0, -1))

    def ray(y, x, dy, dx, c):
        y += 2 * dy
        x += 2 * dx
        while 0 <= y < H and 0 <= x < W and g[y, x] == BG:
            out[y, x] = c
            y += dy
            x += dx

    for y, x, c in centres:
        for dy, dx in minor:
            ray(y, x, dy, dx, c)
    for y, x, c in centres:
        for dy, dx in major:
            ray(y, x, dy, dx, c)
    return out.tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    arm = int(palette[3])
    domv = (int(d4) % 4) in (0, 2)
    return (TEMPLATE.replace('__BG__', str(bg))
            .replace('__ARM__', str(arm))
            .replace('__DOMV__', 'True' if domv else 'False'))
