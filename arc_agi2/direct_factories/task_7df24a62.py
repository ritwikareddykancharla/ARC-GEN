def build_program(d4, palette):
    bg = int(palette[0])
    fr = int(palette[1])
    dot = int(palette[4])
    src = '''import numpy as np

BG = __BG__
FRAME = __FR__
DOT = __DOT__


def _orientations(p):
    pats = []
    q = p
    for _ in range(4):
        for r in (q, q[:, ::-1]):
            if not any(r.shape == s.shape and np.array_equal(r, s) for s in pats):
                pats.append(r.copy())
        q = np.rot90(q)
    return pats


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    pos = np.argwhere(g == FRAME)
    if len(pos) == 0:
        return out.tolist()
    y0, x0 = pos.min(0)
    y1, x1 = pos.max(0)
    if y1 - y0 < 2 or x1 - x0 < 2:
        return out.tolist()
    pat = g[y0 + 1:y1, x0 + 1:x1] == DOT
    if not pat.any():
        return out.tolist()
    isdot = g == DOT
    for p in _orientations(pat):
        h, w = p.shape
        for ty in range(H - h + 1):
            for tx in range(W - w + 1):
                sub = g[ty:ty + h, tx:tx + w]
                if not np.array_equal(isdot[ty:ty + h, tx:tx + w], p):
                    continue
                if not (sub[~p] == BG).all():
                    continue
                cells = []
                ok = True
                for yy in range(ty - 1, ty + h + 1):
                    for xx in range(tx - 1, tx + w + 1):
                        if ty <= yy < ty + h and tx <= xx < tx + w:
                            continue
                        if 0 <= yy < H and 0 <= xx < W:
                            if g[yy, xx] != BG:
                                ok = False
                                break
                            cells.append((yy, xx))
                    if not ok:
                        break
                if not ok:
                    continue
                for yy, xx in cells:
                    out[yy, xx] = FRAME
                reg = out[ty:ty + h, tx:tx + w]
                reg[~p] = FRAME
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__FR__', str(fr)).replace('__DOT__', str(dot))
