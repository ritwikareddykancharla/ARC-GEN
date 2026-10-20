def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    c1 = int(palette[1])
    c2 = int(palette[2])
    # A row reversal swaps the main diagonal and anti-diagonal of a 2x2 block.
    # So does a quarter turn. A half turn leaves the pattern unchanged.
    swapped = ((d4 >= 4) != ((d4 % 4) % 2 == 1))
    if swapped:
        motif = [[c2, c1], [c1, c2]]
    else:
        motif = [[c1, c2], [c2, c1]]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MOTIF = %r' % (motif,))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    out = np.full((2 * h, 2 * w), BG, dtype=int)')
    lines.append('    m = np.array(MOTIF, dtype=int)')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if g[y, x] != BG:')
    lines.append('                out[2 * y:2 * y + 2, 2 * x:2 * x + 2] = m')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
