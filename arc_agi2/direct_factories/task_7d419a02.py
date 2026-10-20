def build_program(d4, palette):
    Z = int(palette[0])
    E = int(palette[8])
    P = int(palette[6])
    Y = int(palette[4])
    src = r'''
import numpy as np

ZERO = __Z__
BASE = __E__
PINK = __P__
MARK = __Y__


def _periodic_separators(g, axis):
    # axis 0: separator ROWS at indices 0,3,6,...; axis 1: separator COLUMNS.
    n = g.shape[axis]
    if n % 3 != 1:
        return False
    for i in range(0, n, 3):
        line = g[i, :] if axis == 0 else g[:, i]
        if not np.all(line == ZERO):
            return False
    return True


def _pink_aligned(coords):
    lo, hi = int(coords.min()), int(coords.max())
    return lo % 3 == 1 and hi == lo + 1


def _interior_zero_lines(g, axis):
    n = g.shape[axis]
    c = 0
    for i in range(1, n - 1):
        line = g[i, :] if axis == 0 else g[:, i]
        if np.all(line == ZERO):
            c += 1
    return c


def _strip_ids_periodic(n):
    return [(-1 if i % 3 == 0 else i // 3) for i in range(n)]


def _strip_ids_runs(g, axis):
    n = g.shape[axis]
    ids = [-1] * n
    cur = -1
    prev_nonzero = False
    for i in range(n):
        line = g[i, :] if axis == 0 else g[:, i]
        nz = bool(np.any(line != ZERO))
        if nz:
            if not prev_nonzero:
                cur += 1
            ids[i] = cur
        prev_nonzero = nz
    return ids


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    ys, xs = np.nonzero(g == PINK)
    if len(ys) == 0:
        return out.tolist()

    # Decide which visible axis carries the separator lines.
    row_sep = _periodic_separators(g, 0)
    col_sep = _periodic_separators(g, 1)
    cand_rows = row_sep and _pink_aligned(ys)
    cand_cols = col_sep and _pink_aligned(xs)
    if cand_rows and not cand_cols:
        axis, periodic = 0, True
    elif cand_cols and not cand_rows:
        axis, periodic = 1, True
    else:
        zr = _interior_zero_lines(g, 0)
        zc = _interior_zero_lines(g, 1)
        axis = 0 if zr >= zc else 1
        periodic = row_sep if axis == 0 else col_sep

    # axis == 0: strips are horizontal bands of rows; the cone widens along columns.
    # axis == 1: strips are vertical bands of columns; the cone widens along rows.
    if axis == 0:
        ids = _strip_ids_periodic(H) if periodic else _strip_ids_runs(g, 0)
        k = ids[int(ys.min())]
        a0, a1 = int(xs.min()), int(xs.max())
        for r in range(H):
            s = ids[r]
            if s < 0:
                continue
            d = abs(s - k)
            if d == 0:
                continue
            lo = a0 - 2 * (d - 1)
            hi = a1 + 2 * (d - 1)
            for c in range(W):
                if g[r, c] == BASE and (c < lo or c > hi):
                    out[r, c] = MARK
    else:
        ids = _strip_ids_periodic(W) if periodic else _strip_ids_runs(g, 1)
        k = ids[int(xs.min())]
        a0, a1 = int(ys.min()), int(ys.max())
        for c in range(W):
            s = ids[c]
            if s < 0:
                continue
            d = abs(s - k)
            if d == 0:
                continue
            lo = a0 - 2 * (d - 1)
            hi = a1 + 2 * (d - 1)
            for r in range(H):
                if g[r, c] == BASE and (r < lo or r > hi):
                    out[r, c] = MARK
    return out.tolist()
'''
    src = src.replace('__Z__', str(Z)).replace('__E__', str(E))
    src = src.replace('__P__', str(P)).replace('__Y__', str(Y))
    return src
