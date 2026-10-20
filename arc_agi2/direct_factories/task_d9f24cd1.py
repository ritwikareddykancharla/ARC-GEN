def build_program(d4, palette):
    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    ur, uc = tf((-1, 0))
    sr, sc = tf((0, 1))
    red = int(palette[2])
    grey = int(palette[5])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('UR, UC = %d, %d' % (ur, uc))
    lines.append('SR, SC = %d, %d' % (sr, sc))
    lines.append('RED = %d' % red)
    lines.append('GREY = %d' % grey)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    H, W = g.shape')
    lines.append('    if UR == -1:')
    lines.append('        base = [(H - 1, c) for c in range(W)]')
    lines.append('    elif UR == 1:')
    lines.append('        base = [(0, c) for c in range(W)]')
    lines.append('    elif UC == -1:')
    lines.append('        base = [(r, W - 1) for r in range(H)]')
    lines.append('    else:')
    lines.append('        base = [(r, 0) for r in range(H)]')
    lines.append('    seeds = [p for p in base if g[p[0], p[1]] == RED]')
    lines.append('    for r, c in seeds:')
    lines.append('        out[r, c] = RED')
    lines.append('        while True:')
    lines.append('            nr, nc = r + UR, c + UC')
    lines.append('            if not (0 <= nr < H and 0 <= nc < W):')
    lines.append('                break')
    lines.append('            if out[nr, nc] == GREY:')
    lines.append('                tr, tc = r + SR, c + SC')
    lines.append('                if not (0 <= tr < H and 0 <= tc < W):')
    lines.append('                    break')
    lines.append('                r, c = tr, tc')
    lines.append('            else:')
    lines.append('                r, c = nr, nc')
    lines.append('            out[r, c] = RED')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
