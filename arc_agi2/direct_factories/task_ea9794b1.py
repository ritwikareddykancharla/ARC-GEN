def build_program(d4, palette):
    pal = [int(x) for x in palette]
    bg = pal[0]
    # Overlay priority from the constructor's painting order (last painted wins):
    # 4 painted first, then 8, then 9, then 3 -> priority 3 > 9 > 8 > 4.
    priority = [pal[3], pal[9], pal[8], pal[4]]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('PRIORITY = %r  # highest first' % (priority,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    h, w = H // 2, W // 2')
    lines.append('    quads = [g[:h, :w], g[:h, W - w:], g[H - h:, :w], g[H - h:, W - w:]]')
    lines.append('    out = np.full((h, w), BG, dtype=int)')
    lines.append('    # Fallback: colours outside the known layer set go underneath everything.')
    lines.append('    for q in quads:')
    lines.append('        m = (q != BG) & ~np.isin(q, PRIORITY)')
    lines.append('        out[m] = q[m]')
    lines.append('    # Paint from lowest priority to highest so higher layers win.')
    lines.append('    for c in reversed(PRIORITY):')
    lines.append('        for q in quads:')
    lines.append('            m = (q == c)')
    lines.append('            out[m] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
