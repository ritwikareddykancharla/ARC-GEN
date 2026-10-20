def build_program(d4, palette):
    k = int(d4) % 4
    # The native rule reverses the vertical axis (row order).
    # Reversing each row first (d4>=4) commutes with reversing the row order.
    # A clockwise rotation by 1 or 3 quarter turns maps the vertical axis onto
    # the horizontal one. The visible rule then reverses column order.
    # Colours are only moved, never recoloured, so the palette is irrelevant.
    axis = 0 if k in (0, 2) else 1
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('AXIS = %d  # 0: swap rows top<->bottom, 1: swap columns left<->right' % axis)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    if g.ndim != 2 or g.size == 0:')
    lines.append('        return [list(r) for r in grid]')
    lines.append('    if AXIS == 0:')
    lines.append('        n = g.shape[0]')
    lines.append('        for i in range(n // 2):')
    lines.append('            j = n - 1 - i')
    lines.append('            g[[i, j], :] = g[[j, i], :]')
    lines.append('    else:')
    lines.append('        n = g.shape[1]')
    lines.append('        for i in range(n // 2):')
    lines.append('            j = n - 1 - i')
    lines.append('            g[:, [i, j]] = g[:, [j, i]]')
    lines.append('    return g.astype(int).tolist()')
    lines.append('')
    return '\n'.join(lines)
