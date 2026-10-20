TEMPLATE = '''import numpy as np

BG = __BG__
RED = __RED__
ANCHOR = __ANC__
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(g, H, W):
    seen = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if seen[y][x] or v == BG or v == RED:
                continue
            seen[y][x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in STEPS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx]:
                        w = g[ny][nx]
                        if w != BG and w != RED:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
            comps.append(sorted(cells))
    return comps


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in np.asarray(grid).tolist()]
    H = len(g)
    W = len(g[0]) if H else 0
    comps = _components(g, H, W)
    if not comps:
        return [row[:] for row in g]
    n = len(comps)
    marks = [set() for _ in range(n)]
    for y in range(H):
        for x in range(W):
            if g[y][x] != RED:
                continue
            bi, bd = -1, None
            for i, body in enumerate(comps):
                d = min(abs(y - a) + abs(x - b) for a, b in body)
                if bd is None or d < bd:
                    bd, bi = d, i
            marks[bi].add((y, x))
    anchors = [i for i, b in enumerate(comps)
               if all(g[y][x] == ANCHOR for y, x in b)]
    if not anchors:
        raise ValueError('no anchor piece')
    anchor = max(anchors, key=lambda i: (len(comps[i]), -i))
    bodies = [frozenset(c) for c in comps]
    markl = [sorted(m) for m in marks]
    nreds = [len(m) for m in marks]
    boxes = []
    kinds = []
    first = {}
    for i in range(n):
        cells = list(bodies[i]) + markl[i]
        y0 = min(c[0] for c in cells)
        x0 = min(c[1] for c in cells)
        y1 = max(c[0] for c in cells)
        x1 = max(c[1] for c in cells)
        boxes.append((y0, x0, y1, x1))
        key = (frozenset((y - y0, x - x0, g[y][x]) for y, x in bodies[i]),
               frozenset((y - y0, x - x0) for y, x in markl[i]))
        kinds.append(first.setdefault(key, i))
    cache = {}

    def moved(i, dy, dx):
        k = (i, dy, dx)
        if k not in cache:
            y0, x0, y1, x1 = boxes[i]
            if y0 + dy < 0 or x0 + dx < 0 or y1 + dy >= H or x1 + dx >= W:
                cache[k] = None
            else:
                cache[k] = (frozenset((y + dy, x + dx) for y, x in bodies[i]),
                            frozenset((y + dy, x + dx) for y, x in markl[i]))
        return cache[k]

    failed = set()

    def rec(remaining, occ, opened, closed, placed):
        if not opened:
            return placed if not remaining else None
        if not remaining:
            return None
        if sum(nreds[i] for i in remaining) < len(opened):
            return None
        key = (occ, opened, closed, tuple(sorted(kinds[i] for i in remaining)))
        if key in failed:
            return None
        reps = {}
        for i in sorted(remaining):
            reps.setdefault(kinds[i], i)
        best = None
        for s in sorted(opened):
            cands = []
            for i in sorted(reps.values()):
                for my, mx in markl[i]:
                    dy, dx = s[0] - my, s[1] - mx
                    got = moved(i, dy, dx)
                    if got is None:
                        continue
                    body, mk = got
                    if not (body.isdisjoint(occ) and body.isdisjoint(opened)
                            and body.isdisjoint(closed)):
                        continue
                    if not (mk.isdisjoint(occ) and mk.isdisjoint(closed)):
                        continue
                    cands.append((-len(mk & opened), i, dy, dx, body, mk))
            if not cands:
                failed.add(key)
                return None
            if best is None or len(cands) < len(best):
                best = cands
                if len(best) == 1:
                    break
        best.sort(key=lambda c: c[:4])
        for _, i, dy, dx, body, mk in best:
            matched = mk & opened
            r = rec(remaining - {i}, occ | body,
                    (opened - matched) | (mk - matched), closed | matched,
                    placed + [(i, dy, dx)])
            if r is not None:
                return r
        failed.add(key)
        return None

    remaining = frozenset(i for i in range(n) if i != anchor)
    res = rec(remaining, bodies[anchor], frozenset(marks[anchor]),
              frozenset(), [(anchor, 0, 0)])
    if res is None:
        raise ValueError('no complete connector assembly')
    out = [[BG] * W for _ in range(H)]
    for i, dy, dx in res:
        for y, x in bodies[i]:
            out[y + dy][x + dx] = g[y][x]
    for i, dy, dx in res:
        for y, x in markl[i]:
            out[y + dy][x + dx] = RED
    return out
'''


def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    anc = int(palette[4])
    src = TEMPLATE.replace('__BG__', str(bg))
    src = src.replace('__RED__', str(red))
    src = src.replace('__ANC__', str(anc))
    return src
