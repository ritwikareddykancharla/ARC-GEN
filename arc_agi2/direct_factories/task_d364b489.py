def build_program(d4, palette):
    def tf(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    base = [(-1, 0, 2), (0, -1, 7), (0, 1, 6), (1, 0, 8)]
    arms = []
    for dr, dc, c in base:
        ndr, ndc = tf(dr, dc)
        arms.append((int(ndr), int(ndc), int(palette[c])))
    bg = int(palette[0])
    seed = int(palette[1])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %r' % bg)
    lines.append('SEED = %r' % seed)
    lines.append('ARMS = %r' % (arms,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    h, w = g.shape')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if g[y, x] != SEED:')
    lines.append('                continue')
    lines.append('            for dy, dx, c in ARMS:')
    lines.append('                ny, nx = y + dy, x + dx')
    lines.append('                if 0 <= ny < h and 0 <= nx < w and g[ny, nx] == BG:')
    lines.append('                    out[ny, nx] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
