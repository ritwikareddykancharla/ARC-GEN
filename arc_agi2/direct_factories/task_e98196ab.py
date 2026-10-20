def build_program(d4, palette):
    k = d4 % 4
    # Horizontal flip (d4>=4) keeps the top half on top; each clockwise turn moves it:
    # k=0 top, k=1 right, k=2 bottom, k=3 left.
    axis = 'row' if k % 2 == 0 else 'col'
    primary_first = k in (0, 3)
    bg = int(palette[0])
    div = int(palette[5])
    src = '''import numpy as np

BG = __BG__
DIV = __DIV__
AXIS = __AXIS__
PRIMARY_FIRST = __PF__


def _lines(g, axis):
    H, W = g.shape
    if axis == 'row':
        return [y for y in range(H) if bool(np.all(g[y, :] == DIV))]
    return [x for x in range(W) if bool(np.all(g[:, x] == DIV))]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    axis = AXIS
    found = _lines(g, axis)
    if not found:
        other = 'col' if axis == 'row' else 'row'
        alt = _lines(g, other)
        if alt:
            axis, found = other, alt
    if found:
        d = found[0]
    else:
        d = (g.shape[0] if axis == 'row' else g.shape[1]) // 2
    if axis == 'row':
        first = g[:d, :]
        second = g[d + 1:, :]
    else:
        first = g[:, :d]
        second = g[:, d + 1:]
    if PRIMARY_FIRST:
        prim, sec = first, second
    else:
        prim, sec = second, first
    out = prim.copy()
    h = min(prim.shape[0], sec.shape[0])
    w = min(prim.shape[1], sec.shape[1])
    region = out[:h, :w]
    s = sec[:h, :w]
    mask = (region == BG) & (s != BG)
    region[mask] = s[mask]
    out[:h, :w] = region
    return out.tolist()
'''
    src = src.replace('__BG__', repr(bg))
    src = src.replace('__DIV__', repr(div))
    src = src.replace('__AXIS__', repr(axis))
    src = src.replace('__PF__', repr(primary_first))
    return src
