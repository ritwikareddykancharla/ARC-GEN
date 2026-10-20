def build_program(d4, palette):
    bg = int(palette[0])
    # Original mechanism: stripes along the top edge are mirrored across the horizontal
    # midline (partner of row r is row H-1-r). Row reversal (d4>=4) keeps that axis.
    # Each clockwise quarter turn swaps it, so odd rotations mirror across the vertical
    # midline (partner of column c is column W-1-c).
    axis = 'rows' if (d4 % 4) % 2 == 0 else 'cols'
    lines = []
    lines.append('BG = %d' % bg)
    lines.append('AXIS = %r' % axis)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = [list(map(int, row)) for row in grid]')
    lines.append('    H = len(g)')
    lines.append('    W = len(g[0]) if H else 0')
    lines.append('    out = [row[:] for row in g]')
    lines.append('    for r in range(H):')
    lines.append('        for c in range(W):')
    lines.append('            if AXIS == \'rows\':')
    lines.append('                pr, pc = H - 1 - r, c')
    lines.append('            else:')
    lines.append('                pr, pc = r, W - 1 - c')
    lines.append('            src = g[pr][pc]')
    lines.append('            if g[r][c] == BG and src != BG:')
    lines.append('                out[r][c] = src')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
