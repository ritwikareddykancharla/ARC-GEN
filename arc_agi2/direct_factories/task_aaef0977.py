def build_program(d4, palette):
    pal = [int(p) for p in palette]
    bg = pal[7]
    cycle = [pal[c] for c in [5, 2, 8, 9, 6, 1, 3, 4, 0]]
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('BG = %d' % bg)
    lines.append('CYCLE = %r' % (cycle,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    bg = BG')
    lines.append('    if not np.any(g == bg):')
    lines.append('        bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])')
    lines.append('    ys, xs = np.where(g != bg)')
    lines.append('    if len(ys) == 0:')
    lines.append('        return g.tolist()')
    lines.append('    sy, sx = int(ys[0]), int(xs[0])')
    lines.append('    seed = int(g[sy, sx])')
    lines.append('    if seed not in CYCLE:')
    lines.append('        return g.tolist()')
    lines.append('    base = CYCLE.index(seed)')
    lines.append('    n = len(CYCLE)')
    lines.append('    out = np.zeros((H, W), dtype=int)')
    lines.append('    for y in range(H):')
    lines.append('        for x in range(W):')
    lines.append('            d = abs(y - sy) + abs(x - sx)')
    lines.append('            out[y, x] = CYCLE[(base + d) % n]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
