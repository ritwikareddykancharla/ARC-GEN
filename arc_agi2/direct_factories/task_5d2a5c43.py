def build_program(d4, palette):
    axis = 'col' if d4 % 4 in (0, 2) else 'row'
    consts = 'import numpy as np\n\nDIV = %d\nMARK = %d\nON = %d\nOFF = %d\nAXIS = %r\n' % (int(palette[1]), int(palette[4]), int(palette[8]), int(palette[0]), axis)
    body = '''

def _seps(g):
    H, W = g.shape
    if AXIS == 'col':
        cands = [x for x in range(W) if (g[:, x] == DIV).all()]
        mid = (W - 1) / 2.0
    else:
        cands = [y for y in range(H) if (g[y, :] == DIV).all()]
        mid = (H - 1) / 2.0
    return cands, mid


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    cands, mid = _seps(g)
    if cands:
        sep = min(cands, key=lambda s: (abs(s - mid), s))
    else:
        sep = int(W // 2) if AXIS == 'col' else int(H // 2)
    if AXIS == 'col':
        a = g[:, :sep]
        b = g[:, sep + 1:]
        w = min(a.shape[1], b.shape[1])
        a = a[:, :w]
        b = b[:, :w]
    else:
        a = g[:sep, :]
        b = g[sep + 1:, :]
        h = min(a.shape[0], b.shape[0])
        a = a[:h, :]
        b = b[:h, :]
    out = np.full(a.shape, OFF, dtype=int)
    out[(a == MARK) | (b == MARK)] = ON
    return out.tolist()
'''
    return consts + body
