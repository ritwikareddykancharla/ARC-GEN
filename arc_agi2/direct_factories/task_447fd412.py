TEMPLATE = '''import numpy as np

BG = __BG__
ONE = __ONE__
TWO = __TWO__
NODE_LIMIT = 200000
SOL_LIMIT = 512


def _comps(mask, diag):
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        steps = steps + [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(sorted(cells))
    return out


def _check(g, cid, sizes, marks, ones, oy, ox, s):
    h, w = g.shape
    ids = set()
    for my, mx in marks:
        for dy in range(s):
            for dx in range(s):
                y = oy + my * s + dy
                x = ox + mx * s + dx
                if not (0 <= y < h and 0 <= x < w):
                    return None
                k = int(cid[y, x])
                if k < 0:
                    return None
                ids.add(k)
    if sum(sizes[k] for k in ids) != len(marks) * s * s:
        return None
    stamp = set()
    for ty, tx in ones:
        for dy in range(s):
            for dx in range(s):
                y = oy + ty * s + dy
                x = ox + tx * s + dx
                if 0 <= y < h and 0 <= x < w:
                    if g[y, x] != BG:
                        return None
                    stamp.add((y, x))
    return (frozenset(ids), frozenset(stamp))


def _placements(g, cid, sizes, targets, marks, ones):
    tried = set()
    found = {}
    for comp in targets:
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        smax = min(max(ys) - min(ys) + 1, max(xs) - min(xs) + 1)
        for py, px in comp:
            for my, mx in marks:
                for s in range(1, smax + 1):
                    key = (py - my * s, px - mx * s, s)
                    if key in tried:
                        continue
                    tried.add(key)
                    res = _check(g, cid, sizes, marks, ones, key[0], key[1], s)
                    if res is not None:
                        found[res] = True
    return list(found.keys())


def _covers(n, plist):
    by_comp = [[] for _ in range(n)]
    for i, pl in enumerate(plist):
        for k in pl[0]:
            by_comp[k].append(i)
    sols = []
    nodes = [0]

    def rec(covered, chosen):
        nodes[0] += 1
        if nodes[0] > NODE_LIMIT or len(sols) > SOL_LIMIT:
            return False
        free = [k for k in range(n) if k not in covered]
        if not free:
            sols.append(tuple(chosen))
            return True
        k = min(free, key=lambda j: (len(by_comp[j]), j))
        for i in by_comp[k]:
            ids = plist[i][0]
            if ids & covered:
                continue
            chosen.append(i)
            ok = rec(covered | ids, chosen)
            chosen.pop()
            if not ok:
                return False
        return True

    complete = rec(frozenset(), [])
    return sols, complete


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    tmpls = [c for c in _comps(g != BG, True) if any(g[y, x] == ONE for y, x in c)]
    if len(tmpls) != 1:
        raise ValueError('No complete visible template/target interpretation')
    tmpl = tmpls[0]
    y0 = min(p[0] for p in tmpl)
    x0 = min(p[1] for p in tmpl)
    ones = [(y - y0, x - x0) for y, x in tmpl if g[y, x] == ONE]
    marks = sorted((y - y0, x - x0) for y, x in tmpl if g[y, x] == TWO)
    if not marks:
        raise ValueError('No complete visible template/target interpretation')
    tset = set(tmpl)
    cid = np.full((H, W), -1, dtype=int)
    targets = []
    sizes = []
    for c in _comps(g == TWO, False):
        if any(p in tset for p in c):
            continue
        for p in c:
            cid[p[0], p[1]] = len(targets)
        targets.append(c)
        sizes.append(len(c))
    if not targets:
        raise ValueError('No complete visible template/target interpretation')
    plist = _placements(g, cid, sizes, targets, marks, ones)
    sols, complete = _covers(len(targets), plist)
    if not complete or not sols:
        raise ValueError('No complete visible template/target interpretation')
    stamps = set()
    for sol in sols:
        cells = set()
        for i in sol:
            cells |= plist[i][1]
        stamps.add(frozenset(cells))
    if len(stamps) != 1:
        raise ValueError('Exact covers disagree on the output')
    final = next(iter(stamps))
    for y, x in final:
        out[y, x] = ONE
    return out.tolist()
'''


def build_program(d4, palette):
    pal = [int(v) for v in palette]
    src = TEMPLATE
    for name, val in (('__BG__', pal[0]), ('__ONE__', pal[1]), ('__TWO__', pal[2])):
        src = src.replace(name, str(val))
    return src
