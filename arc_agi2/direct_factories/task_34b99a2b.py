def build_program(d4, palette):
    horiz = (int(d4) % 4) in (1, 3)
    bg = int(palette[0])
    mark = int(palette[2])
    div = int(palette[4])
    header = (
        'import numpy as np\n'
        'BG = ' + repr(bg) + '\n'
        'MARK = ' + repr(mark) + '\n'
        'DIV = ' + repr(div) + '\n'
        'HORIZ = ' + repr(bool(horiz)) + '\n'
    )
    body = '''
def _pick(cands, n):
    if not cands:
        return n // 2
    mid = (n - 1) / 2.0
    return min(cands, key=lambda t: (abs(t - mid), t))

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    if HORIZ:
        cands = [y for y in range(h) if bool((g[y, :] == DIV).all())]
        k = _pick(cands, h)
        a = g[:k, :]
        b = g[k + 1:, :]
        n = min(a.shape[0], b.shape[0])
        a = a[:n, :]
        b = b[:n, :]
    else:
        cands = [x for x in range(w) if bool((g[:, x] == DIV).all())]
        k = _pick(cands, w)
        a = g[:, :k]
        b = g[:, k + 1:]
        n = min(a.shape[1], b.shape[1])
        a = a[:, :n]
        b = b[:, :n]
    fa = a != BG
    fb = b != BG
    out = np.full(a.shape, BG, dtype=int)
    out[fa != fb] = MARK
    return out.tolist()
'''
    return header + body
