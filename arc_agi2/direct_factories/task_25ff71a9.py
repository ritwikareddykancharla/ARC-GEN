def build_program(d4, palette):
    k = d4 % 4
    # Original motion: one step down, vector (dr, dc) = (1, 0).
    # Reversing each row (d4 >= 4) leaves a vertical vector unchanged.
    # Each clockwise rotation maps (dr, dc) -> (dc, -dr).
    dr, dc = 1, 0
    for _ in range(k):
        dr, dc = dc, -dr
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('DR = %d' % dr)
    lines.append('DC = %d' % dc)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    out = np.full((h, w), BG, dtype=int)')
    lines.append('    # Translate the whole grid one cell along (DR, DC).')
    lines.append('    # Vacated cells become background; content pushed past the edge is dropped.')
    lines.append('    for r in range(h):')
    lines.append('        nr = r + DR')
    lines.append('        if nr < 0 or nr >= h:')
    lines.append('            continue')
    lines.append('        for c in range(w):')
    lines.append('            nc = c + DC')
    lines.append('            if nc < 0 or nc >= w:')
    lines.append('                continue')
    lines.append('            out[nr, nc] = g[r, c]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
