def build_program(d4, palette):
    pal = [int(x) for x in palette]
    bg = pal[0]
    inv = {}
    for i, v in enumerate(pal):
        if v not in inv:
            inv[v] = i
    lines = []
    lines.append('import numpy as np')
    lines.append('BG = %d' % bg)
    lines.append('INV = %r' % (inv,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    vals, counts = np.unique(g, return_counts=True)')
    lines.append('    m = int(counts.min())')
    lines.append('    cands = [int(v) for v, n in zip(vals, counts) if int(n) == m]')
    lines.append('    rare = min(cands, key=lambda v: (INV.get(v, 99), v))')
    lines.append('    out = np.full((h * h, w * w), BG, dtype=int)')
    lines.append('    for r in range(h):')
    lines.append('        for c in range(w):')
    lines.append('            if g[r, c] == rare:')
    lines.append('                out[r * h:(r + 1) * h, c * w:(c + 1) * w] = g')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
