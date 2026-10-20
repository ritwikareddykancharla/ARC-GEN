TEMPLATE = '''import numpy as np

AXIS = __AXIS__
REVERSE = __REV__
DIV = __DIV__
BG = __BG__


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    if AXIS == 'h':
        n = w
        cuts = [x for x in range(w) if bool((g[:, x] == DIV).all())]
    else:
        n = h
        cuts = [y for y in range(h) if bool((g[y, :] == DIV).all())]
    edges = [-1] + cuts + [n]
    spans = [(a + 1, b) for a, b in zip(edges[:-1], edges[1:]) if b - a > 1]
    if REVERSE:
        spans = spans[::-1]

    def piece(s):
        if AXIS == 'h':
            return g[:, s[0]:s[1]]
        return g[s[0]:s[1], :]

    counts = [int((piece(s) != BG).sum()) for s in spans]
    order = sorted(range(len(spans)), key=lambda i: counts[i])
    out = g.copy()
    for slot, src in enumerate(order):
        a, b = spans[slot]
        p = piece(spans[src])
        if AXIS == 'h':
            if p.shape[1] == b - a:
                out[:, a:b] = p
        else:
            if p.shape[0] == b - a:
                out[a:b, :] = p
    return out.tolist()
'''


def build_program(d4, palette):
    dirs = {
        0: ('h', False),
        1: ('v', False),
        2: ('h', True),
        3: ('v', True),
        4: ('h', True),
        5: ('v', True),
        6: ('h', False),
        7: ('v', False),
    }
    axis, rev = dirs[int(d4) % 8]
    div = int(palette[0])
    bg = int(palette[2])
    src = TEMPLATE
    src = src.replace('__AXIS__', repr(axis))
    src = src.replace('__REV__', repr(rev))
    src = src.replace('__DIV__', repr(div))
    src = src.replace('__BG__', repr(bg))
    return src
