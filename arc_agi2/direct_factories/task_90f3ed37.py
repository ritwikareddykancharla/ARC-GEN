TEMPLATE = '''import numpy as np

BG = @BG@
FG = @FG@
FILL = @FILL@

# Bands are anchored on the @START@ edge and continue toward the @END@ edge.
# The complete reference band is the band nearest the @REF@ edge.
# u = cells from the @START@ edge (growth), v = cells from the @REF@ edge (stacking).


def to_uv(y, x, H, W):
    return (@UEXPR@, @VEXPR@)


def to_yx(u, v, H, W):
    return (@YEXPR@, @XEXPR@)


def _profile(cells, v0, s, LU):
    prof = [set() for _ in range(LU)]
    for u, v in cells:
        if v0 <= v < v0 + s:
            prof[u].add(v - v0)
    return [frozenset(p) for p in prof]


def _parse_ref(prof, aw, bw, cw, col0, LU):
    # Reference band = A tiles on [0, col0), one B tile, then C tiles to the far edge.
    if not prof[aw - 1]:
        return None
    for u in range(col0):
        if prof[u] != prof[u % aw]:
            return None
    if not prof[col0 + bw - 1]:
        return None
    e = col0 + bw
    if not prof[e + cw - 1]:
        return None
    for u in range(e, LU):
        if prof[u] != prof[e + (u - e) % cw]:
            return None
    return prof[0:aw], prof[col0:e], prof[e:e + cw]


def _fit_shorts(rest, A, B, C, aw, bw, cw, v0, s, LU, LV):
    # Every other band must be exactly A^k B (same offsets), stacked with gaps.
    ab_min = min(d for col in list(A) + list(B) for d in col)
    remaining = set(rest)
    prev = v0
    paint = set()
    while remaining:
        mv = min(v for _, v in remaining)
        base = mv - ab_min
        if base < prev + s + 1:
            return None
        band = set(p for p in remaining if p[1] < base + s)
        col = max(u for u, _ in band) - (bw - 1)
        if col < aw or col % aw:
            return None
        render = set()
        for c in range(0, col, aw):
            for j in range(aw):
                for d in A[j]:
                    render.add((c + j, base + d))
        for j in range(bw):
            for d in B[j]:
                render.add((col + j, base + d))
        if render != band:
            return None
        e = col + bw
        for u in range(e, LU):
            for d in C[(u - e) % cw]:
                if 0 <= base + d < LV:
                    paint.add((u, base + d))
        remaining -= band
        prev = base
    return frozenset(paint)


def _explanations(cells, LU, LV):
    outs = []
    if not cells:
        return outs
    occupied = set(v for _, v in cells)
    v0 = min(occupied)
    for s in (1, 2, 3):
        if (v0 + s - 1) not in occupied:
            continue
        prof = _profile(cells, v0, s, LU)
        rest = set(p for p in cells if p[1] >= v0 + s)
        for aw in (1, 2):
            for bw in (1, 2):
                for cw in (1, 2):
                    col0 = aw
                    while col0 <= 4 and col0 + bw + cw <= LU:
                        parsed = _parse_ref(prof, aw, bw, cw, col0, LU)
                        if parsed is not None:
                            paint = _fit_shorts(rest, parsed[0], parsed[1], parsed[2], aw, bw, cw, v0, s, LU, LV)
                            if paint is not None:
                                outs.append(paint)
                        col0 += aw
    return outs


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    LU = @LU@
    LV = @LV@
    out = g.copy()
    cells = set()
    for y in range(H):
        for x in range(W):
            if g[y, x] == FG:
                cells.add(to_uv(y, x, H, W))
    outs = _explanations(cells, LU, LV)
    distinct = set(outs)
    if len(distinct) != 1:
        raise ValueError('No unique band continuation output')
    best = next(iter(distinct))
    for u, v in best:
        y, x = to_yx(u, v, H, W)
        if 0 <= y < H and 0 <= x < W and out[y, x] == BG:
            out[y, x] = FILL
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4) % 8
    ey, ex = 0, 1
    ay, ax = 1, 0
    if d4 >= 4:
        ex = -ex
        ax = -ax
    for _ in range(d4 % 4):
        ey, ex = ex, -ey
        ay, ax = ax, -ay
    bg = int(palette[0])
    fg = int(palette[8])
    fill = int(palette[1])
    if ex != 0:
        pos = ex > 0
        rpos = ay > 0
        uexpr = 'x' if pos else '(W - 1 - x)'
        vexpr = 'y' if rpos else '(H - 1 - y)'
        xexpr = 'u' if pos else '(W - 1 - u)'
        yexpr = 'v' if rpos else '(H - 1 - v)'
        lu, lv = 'W', 'H'
        start, end = ('left', 'right') if pos else ('right', 'left')
        refside = 'top' if rpos else 'bottom'
    else:
        pos = ey > 0
        rpos = ax > 0
        uexpr = 'y' if pos else '(H - 1 - y)'
        vexpr = 'x' if rpos else '(W - 1 - x)'
        yexpr = 'u' if pos else '(H - 1 - u)'
        xexpr = 'v' if rpos else '(W - 1 - v)'
        lu, lv = 'H', 'W'
        start, end = ('top', 'bottom') if pos else ('bottom', 'top')
        refside = 'left' if rpos else 'right'
    prog = TEMPLATE
    for key, val in (('@BG@', str(bg)), ('@FG@', str(fg)), ('@FILL@', str(fill)),
                     ('@UEXPR@', uexpr), ('@VEXPR@', vexpr),
                     ('@YEXPR@', yexpr), ('@XEXPR@', xexpr),
                     ('@LU@', lu), ('@LV@', lv),
                     ('@START@', start), ('@END@', end), ('@REF@', refside)):
        prog = prog.replace(key, val)
    return prog
