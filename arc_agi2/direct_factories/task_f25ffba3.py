def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    # In the original frame the grid is mirrored top-to-bottom, and each mirrored
    # colour is stamped only onto background cells.
    # Reversing each row (d4>=4) leaves a top-to-bottom flip unchanged.
    # An odd number of clockwise quarter turns makes it a left-to-right flip.
    if k % 2 == 0:
        flip_expr = 'g[::-1, :]'
        axis_note = 'mirror about the horizontal centre line (reverse row order)'
    else:
        flip_expr = 'g[:, ::-1]'
        axis_note = 'mirror about the vertical centre line (reverse column order)'
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        '',
        'def solve(demonstrations, grid):',
        '    # ' + axis_note + ', then overlay it so that only background cells get filled',
        '    g = np.array(grid, dtype=int)',
        '    mirrored = ' + flip_expr,
        '    out = g.copy()',
        '    mask = (g == BG) & (mirrored != BG)',
        '    out[mask] = mirrored[mask]',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
