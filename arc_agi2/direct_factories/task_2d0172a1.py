def build_program(d4, palette):
    # Work out, for each visible axis, whether it runs opposite to the original axis.
    # The layout treats rows and columns identically, so swapping the axes has no effect.
    # Only the direction of each axis matters. It affects how a block is centred when
    # the free space splits unevenly.
    rev = [False, False]
    if d4 >= 4:
        rev[1] = not rev[1]
    for _ in range(d4 % 4):
        # A clockwise turn sends original (y, x) to (x, H-1-y).
        rev = [rev[1], not rev[0]]
    src = TEMPLATE.replace('__REV0__', 'True' if rev[0] else 'False')
    src = src.replace('__REV1__', 'True' if rev[1] else 'False')
    return src


TEMPLATE = """import numpy as np
from collections import deque

# Per visible axis: True means the centring parity favours the far end.
REV = (__REV0__, __REV1__)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H0, W0 = g.shape
    vals, cnts = np.unique(g, return_counts=True)
    bg = int(vals[int(np.argmax(cnts))])
    others = [int(v) for v in vals if int(v) != bg]
    if not others:
        return g.tolist()
    fg = others[0]
    mask = g != bg
    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    comps = []
    seen = np.zeros((H0, W0), bool)
    for y in range(H0):
        for x in range(W0):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H0 and 0 <= nx < W0 and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(sorted(cells))
    n = len(comps)
    if n == 0:
        return g.tolist()
    encl = []
    esize = []
    for cells in comps:
        wall = np.zeros((H0, W0), bool)
        for y, x in cells:
            wall[y, x] = True
        reach = np.zeros((H0, W0), bool)
        q = deque()
        for y in range(H0):
            for x in range(W0):
                if (y in (0, H0 - 1) or x in (0, W0 - 1)) and not wall[y, x]:
                    reach[y, x] = True
                    q.append((y, x))
        while q:
            y, x = q.popleft()
            for dy, dx in steps:
                ny, nx = y + dy, x + dx
                if 0 <= ny < H0 and 0 <= nx < W0 and not reach[ny, nx] and not wall[ny, nx]:
                    reach[ny, nx] = True
                    q.append((ny, nx))
        e = ~reach & ~wall
        encl.append(e)
        esize.append(int(e.sum()))
    parent = [None] * n
    for i in range(n):
        y, x = comps[i][0]
        best = None
        for j in range(n):
            if j != i and encl[j][y, x]:
                if best is None or esize[j] < esize[best]:
                    best = j
        parent[i] = best
    children = {}
    for j in list(range(n)) + [None]:
        children[j] = [i for i in range(n) if parent[i] == j]
    boxes = []
    for c in comps:
        ys = [p[0] for p in c]
        xs = [p[1] for p in c]
        boxes.append((min(ys), min(xs), max(ys), max(xs)))

    def clusters(ids, a):
        order = sorted(ids, key=lambda i: boxes[i][a])
        idx, k, cur = {}, -1, None
        for i in order:
            if cur is None or boxes[i][a] > cur:
                k += 1
                cur = boxes[i][a + 2]
            else:
                cur = max(cur, boxes[i][a + 2])
            idx[i] = k
        return idx, k + 1

    def shift(p, dy, dx):
        if p[0] == 'dot':
            return ('dot', p[1] + dy, p[2] + dx, p[3])
        return ('frame', p[1] + dy, p[2] + dx, p[3] + dy, p[4] + dx)

    def centre(span, size, axis):
        d = (span - size) // 2
        d -= d % 2
        if REV[axis]:
            return span - size - d
        return d

    def block(i):
        if not children[i]:
            return (3, 3, [('dot', 1, 1, i)])
        h, w, prims, _ = arrange(children[i])
        out = [('frame', 1, 1, h + 2, w + 2)]
        for p in prims:
            out.append(shift(p, 2, 2))
        return (h + 4, w + 4, out)

    def arrange(ids):
        if not ids:
            return (1, 1, [], [])
        ri, nr = clusters(ids, 0)
        ci, nc = clusters(ids, 1)
        blocks = {i: block(i) for i in ids}
        Hs = [1] * nr
        Ws = [1] * nc
        for i in ids:
            Hs[ri[i]] = max(Hs[ri[i]], blocks[i][0])
            Ws[ci[i]] = max(Ws[ci[i]], blocks[i][1])
        rs = [0]
        for r in range(nr - 1):
            rs.append(rs[-1] + Hs[r] - 1)
        cs = [0]
        for c in range(nc - 1):
            cs.append(cs[-1] + Ws[c] - 1)
        total = (rs[-1] + Hs[-1], cs[-1] + Ws[-1])
        places = []
        for i in ids:
            bh, bw, _ = blocks[i]
            oy = rs[ri[i]] + centre(Hs[ri[i]], bh, 0)
            ox = cs[ci[i]] + centre(Ws[ci[i]], bw, 1)
            places.append((i, oy, ox, bh, bw))
        adjusted = []
        for i, oy, ox, bh, bw in places:
            if not children[i]:
                for axis in (0, 1):
                    choices = []
                    for j, jy, jx, jh, jw in places:
                        if j == i or not children[j]:
                            continue
                        same = (ri[i] == ri[j]) if axis == 0 else (ci[i] == ci[j])
                        if not same:
                            continue
                        for prim in blocks[j][2]:
                            if prim[0] != 'dot':
                                continue
                            leaf = prim[3]
                            lo, hi = boxes[i][axis], boxes[i][axis + 2]
                            alo, ahi = boxes[leaf][axis], boxes[leaf][axis + 2]
                            if max(lo, alo) <= min(hi, ahi):
                                coord = (jy if axis == 0 else jx) + prim[axis + 1]
                                choices.append((abs(lo + hi - (alo + ahi)), coord))
                    if choices:
                        dist = min(c[0] for c in choices)
                        anchors = {v for d, v in choices if d == dist}
                        if len(anchors) == 1:
                            offset = next(iter(anchors)) - 1
                            if 0 <= offset <= total[axis] - 3:
                                if axis == 0:
                                    oy = offset
                                else:
                                    ox = offset
            adjusted.append((i, oy, ox, bh, bw))
        prims = []
        for i, oy, ox, bh, bw in adjusted:
            for prim in blocks[i][2]:
                prims.append(shift(prim, oy, ox))
        return (total[0], total[1], prims, adjusted)

    top = children[None]
    _, _, prims, places = arrange(top)
    ys0, xs0, ys1, xs1 = [], [], [], []
    for i, oy, ox, bh, bw in places:
        if children[i]:
            r = (oy + 1, ox + 1, oy + bh - 2, ox + bw - 2)
        else:
            r = (oy, ox, oy + bh - 1, ox + bw - 1)
        ys0.append(r[0])
        xs0.append(r[1])
        ys1.append(r[2])
        xs1.append(r[3])
    Y0, X0 = min(ys0), min(xs0)
    out = np.full((max(ys1) - Y0 + 1, max(xs1) - X0 + 1), bg, dtype=int)
    for p in prims:
        if p[0] == 'dot':
            out[p[1] - Y0, p[2] - X0] = fg
        else:
            y0, x0, y1, x1 = p[1] - Y0, p[2] - X0, p[3] - Y0, p[4] - X0
            out[y0, x0:x1 + 1] = fg
            out[y1, x0:x1 + 1] = fg
            out[y0:y1 + 1, x0] = fg
            out[y0:y1 + 1, x1] = fg
    return out.tolist()
"""
