def build_program(d4, palette):
    d4 = int(d4) % 8
    flip = d4 >= 4
    k = d4 % 4
    # Original output: frame i (ascending count) occupies row i, bar fills columns 0..n-1.
    # Map (row i, col j) through: optional row-reverse, then k clockwise rotations.
    # Each entry is (stack_axis, stack_reversed, bar_from_end).
    table = {
        (False, 0): ('row', False, False),
        (False, 1): ('col', True, False),
        (False, 2): ('row', True, True),
        (False, 3): ('col', False, True),
        (True, 0): ('row', False, True),
        (True, 1): ('col', True, True),
        (True, 2): ('row', True, False),
        (True, 3): ('col', False, False),
    }
    axis, stack_rev, bar_end = table[(flip, k)]
    pal = [int(p) for p in palette]
    bg = pal[0]
    grey = pal[5]
    # Original colour index of each visible colour, used only for a deterministic
    # tie order (ties are outside the constructor's domain).
    rank = {}
    for orig, vis in enumerate(pal):
        if vis not in rank:
            rank[vis] = orig
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('GREY = %d' % grey)
    lines.append('STACK_AXIS = %r' % axis)
    lines.append('STACK_REVERSED = %r' % stack_rev)
    lines.append('BAR_FROM_END = %r' % bar_end)
    lines.append('RANK = %r' % rank)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    colours = sorted(set(int(v) for v in np.unique(g)) - {BG, GREY})')
    lines.append('    info = []')
    lines.append('    for c in colours:')
    lines.append('        ys, xs = np.nonzero(g == c)')
    lines.append('        box = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]')
    lines.append('        n = int((box == GREY).sum())')
    lines.append('        info.append((n, RANK.get(c, c), c))')
    lines.append('    info.sort()')
    lines.append('    F = len(info)')
    lines.append('    if F == 0:')
    lines.append('        return [[BG]]')
    lines.append('    M = max(1, max(n for n, _, _ in info))')
    lines.append('    if STACK_AXIS == "row":')
    lines.append('        out = np.full((F, M), BG, dtype=int)')
    lines.append('    else:')
    lines.append('        out = np.full((M, F), BG, dtype=int)')
    lines.append('    for idx, (n, _, c) in enumerate(info):')
    lines.append('        pos = F - 1 - idx if STACK_REVERSED else idx')
    lines.append('        if n <= 0:')
    lines.append('            continue')
    lines.append('        if STACK_AXIS == "row":')
    lines.append('            if BAR_FROM_END:')
    lines.append('                out[pos, M - n:] = c')
    lines.append('            else:')
    lines.append('                out[pos, :n] = c')
    lines.append('        else:')
    lines.append('            if BAR_FROM_END:')
    lines.append('                out[M - n:, pos] = c')
    lines.append('            else:')
    lines.append('                out[:n, pos] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
