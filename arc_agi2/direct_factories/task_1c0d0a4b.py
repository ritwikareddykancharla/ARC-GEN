def build_program(d4, palette):
    bg = int(palette[0])
    fg = int(palette[8])
    new = int(palette[2])
    # Lattice geometry: grids are (4h+1)x(4w+1) with separators at indices = 0 mod 4.
    # Under any D4 transform, index i maps to i or (4k - i), so separator indices stay
    # = 0 mod 4 and tile cells stay at indices = 1,2,3 mod 4 on both axes. The visible
    # mechanism is therefore the same per-tile inversion for every d4.
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('NEW = %d' % new)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    for y0 in range(1, H, 4):')
    lines.append('        for x0 in range(1, W, 4):')
    lines.append('            y1 = min(y0 + 3, H)')
    lines.append('            x1 = min(x0 + 3, W)')
    lines.append('            block = g[y0:y1, x0:x1]')
    lines.append('            out[y0:y1, x0:x1] = np.where(block == FG, BG, NEW)')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
