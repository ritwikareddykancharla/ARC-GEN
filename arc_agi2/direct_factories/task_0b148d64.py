def build_program(d4, palette):
    pal = [int(x) for x in palette]
    bg = pal[0]
    inv = {}
    for orig, vis in enumerate(pal):
        if vis not in inv:
            inv[vis] = orig
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('ORIG_INDEX = %r' % (inv,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    vals, counts = np.unique(g, return_counts=True)')
    lines.append('    cands = [(int(c), int(v)) for v, c in zip(vals.tolist(), counts.tolist()) if int(v) != BG]')
    lines.append('    if not cands:')
    lines.append('        return g.tolist()')
    lines.append('    # rarest foreground colour; ties broken like the generator (smallest original colour id)')
    lines.append('    cands.sort(key=lambda t: (t[0], ORIG_INDEX.get(t[1], 99), t[1]))')
    lines.append('    rare = cands[0][1]')
    lines.append('    ys, xs = np.where(g == rare)')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    h, w = y1 - y0 + 1, x1 - x0 + 1')
    lines.append('    canvas = np.full((h, w), BG, dtype=int)')
    lines.append('    canvas[:, :] = g[y0:y1 + 1, x0:x1 + 1]')
    lines.append('    return canvas.tolist()')
    return '\n'.join(lines) + '\n'
