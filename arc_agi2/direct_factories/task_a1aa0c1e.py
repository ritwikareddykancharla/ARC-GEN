def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4
    # Visible direction of the original 'down' (towards the floor).
    # Reversing rows keeps vertical vectors; a clockwise turn maps (dr, dc) -> (dc, -dr).
    dv = (1, 0)
    for _ in range(k):
        dv = (dv[1], -dv[0])
    axis = 0 if dv[0] != 0 else 1
    sign = dv[0] + dv[1]

    # Visible placement of output cell (stratum i, slot j) as an affine form in 1, i, j, (n-1).
    def add(a, b, s):
        out = dict(a)
        for key, v in b.items():
            out[key] = out.get(key, 0) + s * v
        return out

    def m1(d):
        return {'N1': 1} if d == 'N' else {'1': 4}

    r = {'i': 1}
    c = {'j': 1}
    h, w = 'N', '5'
    if flip:
        c = add(m1(w), c, -1)
    for _ in range(k):
        r, c = c, add(m1(h), r, -1)
        h, w = w, h
    rc = [r.get('1', 0), r.get('i', 0), r.get('j', 0), r.get('N1', 0)]
    cc = [c.get('1', 0), c.get('i', 0), c.get('j', 0), c.get('N1', 0)]
    sor = (h == 'N')

    template = '''import numpy as np

AXIS = @AXIS@
SIGN = @SIGN@
RC = @RC@
CC = @CC@
STRATA_ON_ROWS = @SOR@
MARKER_C = @MARKER@
BG = @BG@
FLOOR_C = @FLOOR@
RANK = 0
RUNGS = 1


def _predict(grid, mode):
    g = np.array(grid, dtype=int)
    if g.ndim != 2 or g.size == 0:
        raise ValueError('Expected a non-empty rectangular grid')
    bg = BG
    L = g.shape[0] if AXIS == 0 else g.shape[1]

    def lane(p):
        return g[p, :] if AXIS == 0 else g[:, p]

    lines = []
    for p in range(L):
        a = lane(p)
        if int(a[0]) != bg and bool((a == a[0]).all()):
            lines.append(p)
    if SIGN < 0:
        lines = lines[::-1]
    if len(lines) != 4:
        raise ValueError('Expected three levels and one floor')
    floor_c = int(lane(lines[-1])[0])
    if floor_c != FLOOR_C:
        raise ValueError('The final level must be the floor')
    strata = lines[:-1]
    n = len(strata)
    line_cols = set(int(lane(p)[0]) for p in lines)
    others = sorted(set(int(v) for v in np.unique(g)) - line_cols - set([bg]))
    if others != [MARKER_C]:
        raise ValueError('Expected the single climber colour')
    marker = MARKER_C

    colours = []
    lengths = []
    rungs = []
    reaches = []
    for idx, p in enumerate(strata):
        col = int(lane(p)[0])
        q = lines[idx + 1]
        t = p + SIGN
        ln = 0
        rg = 0
        while t != q:
            hit = int((lane(t) == col).sum())
            if hit == 0:
                break
            if hit >= 3:
                rg += 1
            ln += 1
            t += SIGN
        colours.append(col)
        lengths.append(ln)
        rungs.append(rg)
        reaches.append(ln > 0 and ln == abs(q - p) - 1)

    if mode == RANK:
        s = sorted(lengths)
        cells = []
        for ln in lengths:
            if ln == 0:
                cells.append(0)
            elif ln == s[n // 2]:
                cells.append(2)
            elif ln == s[0]:
                cells.append(1)
            else:
                cells.append(3)
    else:
        cells = [min(rg, 3) for rg in rungs]

    top = n - 1
    for i in range(n - 1, -1, -1):
        if reaches[i]:
            top = i
        else:
            break

    shape = (n, 5) if STRATA_ON_ROWS else (5, n)
    out = np.full(shape, bg, dtype=int)

    def put(i, j, v):
        rr = RC[0] + RC[1] * i + RC[2] * j + RC[3] * (n - 1)
        c2 = CC[0] + CC[1] * i + CC[2] * j + CC[3] * (n - 1)
        out[rr, c2] = v

    for i in range(n):
        put(i, 3, floor_c)
        for j in range(min(cells[i], 3)):
            put(i, j, colours[i])
    put(top, 4, marker)
    return out.tolist()


def solve(demonstrations, grid):
    if not demonstrations:
        raise ValueError('Demonstrations required')
    alive = [mode for mode in (RANK, RUNGS)
             if all(_predict(p['input'],mode) == p['output'] for p in demonstrations)]
    if not alive:
        raise ValueError('Neither ladder rule fits all demonstrations')
    predictions = [_predict(grid,mode) for mode in alive]
    if any(out != predictions[0] for out in predictions[1:]):
        raise ValueError('Demonstrations do not distinguish ladder length rank from rung count')
    return predictions[0]
'''
    src = template.replace('@AXIS@', repr(axis))
    src = src.replace('@SIGN@', repr(sign))
    src = src.replace('@RC@', repr(rc))
    src = src.replace('@CC@', repr(cc))
    src = src.replace('@SOR@', repr(sor))
    src = src.replace('@MARKER@', repr(int(palette[5])))
    src = src.replace('@BG@', repr(int(palette[0])))
    src = src.replace('@FLOOR@', repr(int(palette[9])))
    return src
