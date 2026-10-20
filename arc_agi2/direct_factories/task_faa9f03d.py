TEMPLATE = '''import numpy as np

BG = @BG@
CORNER = @CORNER@
MARK = @MARK@
# Order in which the four neighbours of a 4-marker are tried, in visible coordinates.
MARKER_DIRS = @DIRS@
# Tie-break key for layer ordering: the native solver uses the colour number.
NATIVE_RANK = @RANK@


def _rank(c):
    return NATIVE_RANK.get(c, 10 + c)


def _build(g, c):
    # Rebuild path c from row and column runs of c or CORNER cells.
    H, W = g.shape
    s = set()

    def isc(y, x):
        return 0 <= y < H and 0 <= x < W and int(g[y, x]) in (c, CORNER)

    for axis in (0, 1):
        L = H if axis == 0 else W
        for i in range(L):
            if axis == 0:
                line = [int(v) for v in g[i, :]]
                pos = (lambda j, i=i: (i, j))
            else:
                line = [int(v) for v in g[:, i]]
                pos = (lambda j, i=i: (j, i))
            n = len(line)

            def blocked(j, axis=axis, pos=pos):
                # Cell j is the middle of a perpendicular stretch of c.
                y, x = pos(j)
                if int(g[y, x]) != c:
                    return False
                if axis == 0:
                    return isc(y - 1, x) and isc(y + 1, x)
                return isc(y, x - 1) and isc(y, x + 1)

            xs = [j for j in range(n) if line[j] in (c, CORNER)]
            groups = []
            for j in xs:
                if groups:
                    prev = groups[-1][-1]
                    if j - prev == 1 or (j - prev == 2 and (not blocked(j)) and (not blocked(prev))):
                        groups[-1].append(j)
                        continue
                groups.append([j])
            for grp in groups:
                if sum(1 for j in grp if line[j] == c) < 2:
                    continue
                for j in range(grp[0], grp[-1] + 1):
                    s.add(pos(j))
    return s


def _apply_markers(g, S, cols, ext):
    # Each 4 reverses the limb that leaves the adjacent corner K.
    H, W = g.shape
    fours = [(int(y), int(x)) for y, x in zip(*np.where(g == MARK))]
    for y, x in fours:
        done = False
        for dy, dx in MARKER_DIRS:
            K = (y + dy, x + dx)
            O = (K[0] + dy, K[1] + dx)
            for c in cols:
                if K in S[c] and O in S[c]:
                    rest = S[c] - {K}
                    comp = {O}
                    stack = [O]
                    while stack:
                        p = stack.pop()
                        for ay, ax in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            q = (p[0] + ay, p[1] + ax)
                            if q in rest and q not in comp:
                                comp.add(q)
                                stack.append(q)
                    S[c] -= comp
                    yy, xx = K
                    while 0 <= yy < H and 0 <= xx < W:
                        S[c].add((yy, xx))
                        yy -= dy
                        xx -= dx
                    ext.setdefault(c, set()).add('h' if dx else 'v')
                    done = True
                    break
            if done:
                break


def _reaches(a, b, edges):
    seen = {a}
    todo = [a]
    while todo:
        p = todo.pop()
        for u, v in edges:
            if u == p and v not in seen:
                seen.add(v)
                todo.append(v)
    return b in seen


def _paint(g, S, cols, ext):
    # Edge (a, b) means a is painted below b.
    def axis(c, y, x):
        horizontal = (y, x - 1) in S[c] and (y, x + 1) in S[c]
        vertical = (y - 1, x) in S[c] and (y + 1, x) in S[c]
        if horizontal and not vertical:
            return 'h'
        if vertical and not horizontal:
            return 'v'
        return None

    edges = set()
    # Pass 1: at blank crossings, the strand parallel to a redirect wins.
    for i, c in enumerate(cols):
        for d in cols[i + 1:]:
            for (y, x) in sorted(S[c] & S[d]):
                if int(g[y, x]) != BG:
                    continue
                ac, ad = axis(c, y, x), axis(d, y, x)
                preferred = set()
                for col, la in ((c, ac), (d, ad)):
                    if la in ext.get(col, set()):
                        preferred.add(la)
                if not preferred:
                    preferred = set(a for axes in ext.values() for a in axes)
                if ac in preferred and ad not in preferred:
                    edge = (d, c)
                elif ad in preferred and ac not in preferred:
                    edge = (c, d)
                else:
                    continue
                if not _reaches(edge[1], edge[0], edges):
                    edges.add(edge)
    # Pass 2: a visible crossing colour marks the LOWER path.
    for i, c in enumerate(cols):
        for d in cols[i + 1:]:
            for (y, x) in sorted(S[c] & S[d]):
                v = int(g[y, x])
                if v == c:
                    edge = (c, d)
                elif v == d:
                    edge = (d, c)
                else:
                    continue
                if not _reaches(edge[1], edge[0], edges):
                    edges.add(edge)
    order = []
    remaining = set(cols)
    while remaining:
        available = [c for c in remaining if not any(b == c and a in remaining for a, b in edges)]
        if not available:
            available = list(remaining)
        pick = min(available, key=lambda col: (-len(S[col]), _rank(col)))
        order.append(pick)
        remaining.remove(pick)
    out = np.full(g.shape, BG, dtype=int)
    for c in order:
        for (y, x) in S[c]:
            out[y, x] = c
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    present = sorted(set(int(v) for v in g.ravel().tolist()))
    cols = [c for c in present if c not in (BG, CORNER, MARK)]
    cols.sort(key=_rank)
    S = {c: _build(g, c) for c in cols}
    ext = {}
    _apply_markers(g, S, cols, ext)
    out = _paint(g, S, cols, ext)
    return out.tolist()
'''


def build_program(d4, palette):
    def pc(c):
        try:
            return int(palette[c])
        except Exception:
            return int(c)
    bg = pc(0)
    corner = pc(2)
    mark = pc(4)
    rank = {}
    for c in range(10):
        v = pc(c)
        if v not in rank:
            rank[v] = c
    k = int(d4) % 4
    flip = int(d4) >= 4

    def tdir(d):
        dr, dc = d
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return (dr, dc)

    dirs = [tdir(d) for d in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    src = TEMPLATE
    src = src.replace('@BG@', repr(bg))
    src = src.replace('@CORNER@', repr(corner))
    src = src.replace('@MARK@', repr(mark))
    src = src.replace('@DIRS@', repr(dirs))
    src = src.replace('@RANK@', repr(rank))
    return src
