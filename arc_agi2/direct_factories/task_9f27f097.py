def build_program(d4, palette):
    hole = int(palette[0])
    # In the original orientation the copy is reversed along columns (left-right mirror).
    # Conjugating a left-right mirror by any D4 element gives a left-right mirror for
    # even rotation counts and an up-down mirror for odd rotation counts.
    # The pre-reflection used by indices >= 4 commutes with the left-right mirror.
    flip_rows = (int(d4) % 4) % 2 == 1
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('')
    lines.append('HOLE = %d' % hole)
    lines.append('FLIP_ROWS = %s' % ('True' if flip_rows else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])')
    lines.append('    zy, zx = np.where(g == HOLE)')
    lines.append('    if zy.size == 0:')
    lines.append('        return out.tolist()')
    lines.append('    hy0, hy1, hx0, hx1 = zy.min(), zy.max(), zx.min(), zx.max()')
    lines.append('    py, px = np.where((g != bg) & (g != HOLE))')
    lines.append('    if py.size == 0:')
    lines.append('        return out.tolist()')
    lines.append('    pat = g[py.min():py.max() + 1, px.min():px.max() + 1]')
    lines.append('    if FLIP_ROWS:')
    lines.append('        m = pat[::-1, :]')
    lines.append('    else:')
    lines.append('        m = pat[:, ::-1]')
    lines.append('    h = min(m.shape[0], hy1 - hy0 + 1)')
    lines.append('    w = min(m.shape[1], hx1 - hx0 + 1)')
    lines.append('    out[hy0:hy0 + h, hx0:hx0 + w] = m[:h, :w]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
