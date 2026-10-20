def build_program(d4, palette):
    piece = int(palette[4])
    mark = int(palette[7])
    fill_default = int(palette[1])
    src = '''import numpy as np
from collections import Counter, deque

PIECE = __PIECE__
MARK = __MARK__
FILL_DEFAULT = __FILL__
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _pairs_of(demonstrations):
    res = []
    for d in demonstrations or []:
        try:
            if isinstance(d, dict):
                res.append((d.get('input'), d.get('output')))
            else:
                res.append((d[0], d[1]))
        except Exception:
            pass
    return res


def _fill(g, demonstrations):
    rest = [int(v) for v in g.flatten() if int(v) not in (PIECE, MARK)]
    if rest:
        return Counter(rest).most_common(1)[0][0]
    for _, o in _pairs_of(demonstrations):
        try:
            vals = [int(v) for v in np.asarray(o).flatten() if int(v) not in (PIECE, MARK)]
        except Exception:
            vals = []
        if vals:
            return Counter(vals).most_common(1)[0][0]
    return FILL_DEFAULT


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    fill = _fill(g, demonstrations)
    comps = _components(g != fill)
    groups = []
    for comp in comps:
        ms = [p for p in comp if g[p] == MARK]
        if ms:
            groups.append((sorted(ms), [p for p in comp if g[p] == PIECE]))
    if len(groups) < 2:
        return [list(map(int, row)) for row in g]
    (mA, pA), (mB, pB) = groups[0], groups[1]

    def cands(ms):
        out = []
        for d in DIRS:
            ok = True
            for y, x in ms:
                ny, nx = y + d[0], x + d[1]
                if not (0 <= ny < H and 0 <= nx < W and g[ny, nx] == PIECE):
                    ok = False
                    break
            if ok:
                out.append(d)
        return out

    cA, cB = cands(mA), cands(mB)
    pairs = [(a, b) for a in cA for b in cB if a == (-b[0], -b[1])]
    if pairs:
        dB = pairs[0][1]
    elif cB:
        dB = cB[0]
    elif cA:
        dB = (-cA[0][0], -cA[0][1])
    else:
        dB = (0, 0)
    a0 = min(mA)
    b0 = min(mB)
    sh = (a0[0] - b0[0] - dB[0], a0[1] - b0[1] - dB[1])
    pB2 = [(y + sh[0], x + sh[1]) for y, x in pB]
    allc = list(pA) + pB2
    if not allc:
        return [[fill]]
    y0 = min(c[0] for c in allc)
    x0 = min(c[1] for c in allc)
    y1 = max(c[0] for c in allc)
    x1 = max(c[1] for c in allc)
    out = [[fill] * (x1 - x0 + 1) for _ in range(y1 - y0 + 1)]
    for y, x in allc:
        out[y - y0][x - x0] = PIECE
    return out
'''
    src = src.replace('__PIECE__', str(piece))
    src = src.replace('__MARK__', str(mark))
    src = src.replace('__FILL__', str(fill_default))
    return src
