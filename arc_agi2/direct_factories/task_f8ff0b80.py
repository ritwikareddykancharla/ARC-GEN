def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    # Original output: a 3x1 column listing colours from most cells (top) to fewest (bottom).
    # For d4 >= 4 the horizontal flip is applied first, which does nothing to a width-1 column.
    # Clockwise rotations:
    #   k=0 -> column, most frequent at the top
    #   k=1 -> row, most frequent at the right
    #   k=2 -> column, most frequent at the bottom
    #   k=3 -> row, most frequent at the left
    vertical = k in (0, 2)
    reverse = k in (1, 2)
    lines = [
        'import numpy as np',
        '',
        'BG = %d' % bg,
        'VERTICAL = %r' % vertical,
        'REVERSE = %r' % reverse,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.asarray(grid, dtype=int)',
        '    mask = g != BG',
        '    if not mask.any():',
        '        return [[BG]]',
        '    vals, counts = np.unique(g[mask], return_counts=True)',
        '    # Count cells per colour (not per object). Sort descending; break ties by colour value.',
        '    pairs = sorted(zip(vals.tolist(), counts.tolist()), key=lambda t: (-t[1], t[0]))',
        '    order = [int(v) for v, n in pairs]',
        '    if REVERSE:',
        '        order = order[::-1]',
        '    if VERTICAL:',
        '        return [[c] for c in order]',
        '    return [order]',
        '',
    ]
    return '\n'.join(lines)
