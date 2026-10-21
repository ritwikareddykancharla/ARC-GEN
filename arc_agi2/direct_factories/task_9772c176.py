def build_program(d4, palette):
    # Only the colour roles are specialised. d4 is NOT used: both cap axes
    # are always enumerated and demonstrations must agree with the axis.
    bg = int(palette[0])
    fg = int(palette[8])
    roof = int(palette[4])
    src = r'''
BG = __BG__
FG = __FG__
ROOF = __ROOF__


def _view(g, vert):
    # Frame view: s runs along the cap axis, t across it.
    if vert:
        return [row[:] for row in g]
    return [list(col) for col in zip(*g)]


def _unview(f, vert):
    if vert:
        return [row[:] for row in f]
    return [list(col) for col in zip(*f)]


def _overlaps(a, b):
    (sa, ta, wa, ha, _), (sb, tb, wb, hb, _) = a, b
    if sa + ha + 5 <= sb or sb + hb + 5 <= sa:
        return False
    if ta + wa + 5 <= tb or tb + wb + 5 <= ta:
        return False
    return True


def _render(blobs, La, Lc):
    """Exact re-drawing of the scene in the cap-axis frame.

    blobs: ordered (brow, bcol, wide, tall, trim). Returns (input, output)
    with 0=background, 8=blob, 4=roof, or None when the scene is rejected.
    """
    if _overlaps(blobs[0], blobs[1]):
        return None
    gi = [[0] * Lc for _ in range(La)]
    go = [[0] * Lc for _ in range(La)]

    def put(G, s, t, v):
        if 0 <= s < La and 0 <= t < Lc:
            G[s][t] = v

    def get(G, s, t):
        if 0 <= s < La and 0 <= t < Lc:
            return G[s][t]
        return -1

    for brow, bcol, wide, tall, trim in blobs:
        for s in range(brow, brow + tall):
            for t in range(bcol, bcol + wide):
                put(gi, s, t, 8)
                put(go, s, t, 8)
        bot, top, left, rite, i = brow, brow + tall - 1, bcol, bcol + wide, 0
        while True:
            bot, top, left, rite = bot - 1, top + 1, left + 1, rite - 1
            if left >= rite:
                break
            for t in range(left, rite):
                if get(go, bot, t) in (4, 8) or get(go, top, t) in (4, 8):
                    return None
                if i < trim:
                    put(gi, bot, t, 8)
                    put(gi, top, t, 8)
                    put(go, bot, t, 8)
                    put(go, top, t, 8)
                else:
                    put(go, bot, t, 4)
                    put(go, top, t, 4)
            i += 1
        bot, top, left, rite = brow, brow + tall, bcol, bcol + wide - 1
        while True:
            bot, top, left, rite = bot + 1, top - 1, left - 1, rite + 1
            if bot >= top:
                break
            for s in range(bot, top):
                if get(go, s, left) in (4, 8) or get(go, s, rite) in (4, 8):
                    return None
                put(go, s, left, 4)
                put(go, s, rite, 4)
    return gi, go


def _blob_bits(blob, La, Lc):
    brow, bcol, wide, tall, trim = blob
    bits = 0
    for s in range(brow, brow + tall):
        for t in range(bcol, bcol + wide):
            bits |= 1 << (s * Lc + t)
    for i in range(trim):
        for t in range(bcol + 1 + i, bcol + wide - 1 - i):
            for s in (brow - 1 - i, brow + tall + i):
                if 0 <= s < La:
                    bits |= 1 << (s * Lc + t)
    return bits


def _candidates(F, La, Lc):
    """Blob hypotheses whose 8-cells are all blob-coloured in F.

    A rectangle's interior rows (all but its first/last) are bounded on both
    sides by the blob's own first side-roof layer, which the constructor
    keeps free of 8.  So each interior row is an exact maximal run [t0, t1],
    and the rectangle's first/last row is the end of, or one beyond, a
    maximal block of identical exact runs.
    """
    runs = {}
    for s in range(La):
        t = 0
        row = F[s]
        while t < Lc:
            if row[t] == 8:
                u = t
                while t + 1 < Lc and row[t + 1] == 8:
                    t += 1
                runs.setdefault((u, t), []).append(s)
            t += 1
    mask = 0
    for s in range(La):
        for t in range(Lc):
            if F[s][t] == 8:
                mask |= 1 << (s * Lc + t)
    out = []
    seen = set()
    for (t0, t1), rows in runs.items():
        wide = t1 - t0 + 1
        if wide < 5 or wide > (2 * Lc) // 3 or t0 < 1 or t1 > Lc - 2:
            continue
        blocks = []
        for s in rows:
            if blocks and blocks[-1][1] == s - 1:
                blocks[-1][1] = s
            else:
                blocks.append([s, s])
        for i0, i1 in blocks:
            for ra0 in (i0 - 1, i0):
                for ra1 in (i1, i1 + 1):
                    tall = ra1 - ra0 + 1
                    if tall < 3 or tall > La // 2 or ra0 < 1 or ra1 > La - 2:
                        continue
                    for trim in range(1, (wide - 3) // 2 + 1):
                        blob = (ra0, t0, wide, tall, trim)
                        if blob in seen:
                            continue
                        bits = _blob_bits(blob, La, Lc)
                        if bits & mask == bits:
                            seen.add(blob)
                            out.append((blob, bits))
    return out, mask


def _hypotheses(g, vert):
    """All constructor scenes on this cap axis that redraw the input exactly.

    Returns the set of distinct visible outputs they imply.
    """
    F = _view(g, vert)
    La, Lc = len(F), len(F[0])
    for row in F:
        for v in row:
            if v != 0 and v != 8:
                return set()
    cands, mask = _candidates(F, La, Lc)
    outs = set()
    n = len(cands)
    for i in range(n):
        a, abits = cands[i]
        for j in range(n):
            if i == j:
                continue
            b, bbits = cands[j]
            if abits | bbits != mask:
                continue
            drawn = _render([a, b], La, Lc)
            if drawn is None or drawn[0] != F:
                continue
            o = _unview(drawn[1], vert)
            outs.add(tuple(tuple(r) for r in o))
    return outs


def _to_roles(g):
    res = []
    for row in g:
        r = []
        for v in row:
            v = int(v)
            r.append(0 if v == BG else 8 if v == FG else 4 if v == ROOF else -9)
        res.append(r)
    return res


def _from_roles(g):
    colour = {0: BG, 8: FG, 4: ROOF}
    return [[colour[v] for v in row] for row in g]


def solve(demonstrations, grid):
    query = _to_roles(grid)
    axes = []
    for vert in (True, False):
        ok = True
        for pair in demonstrations:
            outs = _hypotheses(_to_roles(pair['input']), vert)
            want = tuple(tuple(r) for r in _to_roles(pair['output']))
            if want not in outs:
                ok = False
                break
        if ok:
            axes.append(vert)
    if not axes:
        raise ValueError('no cap axis explains every demonstration')
    outs = set()
    for vert in axes:
        outs |= _hypotheses(query, vert)
    if len(outs) != 1:
        raise ValueError('query not identified: %d candidate outputs' % len(outs))
    return _from_roles([list(r) for r in next(iter(outs))])
'''
    src = src.replace('__BG__', str(bg)).replace('__FG__', str(fg))
    src = src.replace('__ROOF__', str(roof))
    return src
