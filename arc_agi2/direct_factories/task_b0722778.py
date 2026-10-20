TEMPLATE = '''import numpy as np

BG = __BG__
STRIPS_ARE_COLUMNS = __COLS__
A_FIRST = __AFIRST__
MIRROR_UPDOWN = __MUD__


def _groups(idx):
    out, cur = [], []
    for i in idx:
        if cur and i != cur[-1] + 1:
            out.append(cur)
            cur = []
        cur.append(i)
    if cur:
        out.append(cur)
    return out


def _identity(a):
    return a


def _mirror_lr(a):
    return a[:, ::-1]


def _mirror_ud(a):
    return a[::-1, :]


def _rot_cw(a):
    return np.rot90(a, -1)


def _rot_ccw(a):
    return np.rot90(a, 1)


def _rot_180(a):
    return a[::-1, ::-1]


def _transpose(a):
    return a.T


def _anti_transpose(a):
    return a[::-1, ::-1].T


if MIRROR_UPDOWN:
    _FAMILY_MIRROR, _OTHER_MIRROR = _mirror_ud, _mirror_lr
else:
    _FAMILY_MIRROR, _OTHER_MIRROR = _mirror_lr, _mirror_ud

# Family transforms first (mirror across the band axis, clockwise, counter-clockwise),
# then the remaining symmetries as a fallback.
_SYMS = [_identity, _FAMILY_MIRROR, _rot_cw, _rot_ccw, _OTHER_MIRROR,
         _rot_180, _transpose, _anti_transpose]


def _colour_map(a, b):
    m = {}
    for u, v in zip(a.ravel().tolist(), b.ravel().tolist()):
        if m.setdefault(int(u), int(v)) != int(v):
            return None
    return m


def _solve_block(A, B, C):
    for f in _SYMS:
        t = f(A)
        if t.shape == B.shape and np.array_equal(t, B):
            return f(C)
    for f in _SYMS:
        t = f(A)
        if t.shape != B.shape:
            continue
        m = _colour_map(t, B)
        if m is not None:
            tc = f(C)
            return np.array([[m.get(int(x), int(x)) for x in row] for row in tc.tolist()], dtype=int)
    return C.copy()


def _block(g, strip_lines, p0, p1):
    s0, s1 = strip_lines[0], strip_lines[-1] + 1
    if STRIPS_ARE_COLUMNS:
        return g[p0:p1, s0:s1]
    return g[s0:s1, p0:p1]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    nb = g != BG
    row_used = [y for y in range(H) if nb[y, :].any()]
    col_used = [x for x in range(W) if nb[:, x].any()]
    if STRIPS_ARE_COLUMNS:
        strips, bands = _groups(col_used), _groups(row_used)
    else:
        strips, bands = _groups(row_used), _groups(col_used)
    if len(strips) < 2 or not bands:
        return g.tolist()
    if A_FIRST:
        a_l, b_l, c_l = strips[0], strips[1], strips[-1]
    else:
        a_l, b_l, c_l = strips[-1], strips[-2], strips[0]
    span = c_l[-1] - c_l[0] + 1
    if STRIPS_ARE_COLUMNS:
        out = np.full((H, span), BG, dtype=int)
    else:
        out = np.full((span, W), BG, dtype=int)
    for band in bands:
        p0, p1 = band[0], band[-1] + 1
        A = _block(g, a_l, p0, p1)
        B = _block(g, b_l, p0, p1)
        C = _block(g, c_l, p0, p1)
        res = _solve_block(A, B, C)
        if res.shape != C.shape:
            res = C.copy()
        if STRIPS_ARE_COLUMNS:
            out[p0:p1, :] = res
        else:
            out[:, p0:p1] = res
    return out.tolist()
'''


def build_program(d4, palette):
    d4 = int(d4)
    k = d4 % 4
    v = (0, -1) if d4 >= 4 else (0, 1)
    for _ in range(k):
        v = (v[1], -v[0])
    cols = (v[0] == 0)
    direction = v[1] if cols else v[0]
    a_first = direction > 0
    mirror_ud = (k % 2 == 1)
    bg = int(palette[0])
    src = TEMPLATE
    src = src.replace('__BG__', str(bg))
    src = src.replace('__COLS__', str(bool(cols)))
    src = src.replace('__AFIRST__', str(bool(a_first)))
    src = src.replace('__MUD__', str(bool(mirror_ud)))
    return src
