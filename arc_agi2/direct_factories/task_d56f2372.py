def build_program(d4, palette):
    k = int(d4) % 4
    # Original rule: the chosen crop equals its left-right mirror (columns reversed).
    # If d4 >= 4, rows are first reversed. That flip commutes with a left-right mirror.
    # A clockwise rotation by an odd k turns the vertical mirror axis horizontal.
    # So the visible test reverses rows when k is odd and columns when k is even.
    axis = 0 if (k % 2 == 1) else 1
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('MIRROR_AXIS = %d  # 1: reverse columns (left-right), 0: reverse rows (up-down)' % axis)
    lines.append('')
    lines.append('def _mirror(sub):')
    lines.append('    if MIRROR_AXIS == 1:')
    lines.append('        return sub[:, ::-1]')
    lines.append('    return sub[::-1, :]')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    cands = []')
    lines.append('    for c in sorted(set(g.ravel().tolist())):')
    lines.append('        if c == BG:')
    lines.append('            continue')
    lines.append('        ys, xs = np.where(g == c)')
    lines.append('        y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('        x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('        sub = g[y0:y1 + 1, x0:x1 + 1]')
    lines.append('        sub = np.where(sub == c, c, BG)')
    lines.append('        sym = bool(np.array_equal(sub, _mirror(sub)))')
    lines.append('        cands.append((sym, int(len(ys)), int(c), sub))')
    lines.append('    if not cands:')
    lines.append('        return g.tolist()')
    lines.append('    sym_c = [t for t in cands if t[0]]')
    lines.append('    pool = sym_c if sym_c else cands')
    lines.append('    best = max(pool, key=lambda t: t[1])')
    lines.append('    return best[3].astype(int).tolist()')
    lines.append('')
    return '\n'.join(lines)
