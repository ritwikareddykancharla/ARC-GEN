def build_program(d4, palette):
    bg = int(palette[0])
    k = int(d4) % 4
    # Original output: n x 1 column, most frequent minority colour at top.
    # A horizontal flip (d4>=4) leaves an n x 1 column unchanged.
    # Clockwise rotation k times then gives:
    #   k=0: column, most frequent first (top -> bottom)
    #   k=1: row, most frequent at the right (descending runs right -> left)
    #   k=2: column, most frequent at the bottom
    #   k=3: row, most frequent at the left
    if k == 0:
        shape_kind, reverse_order = 'col', False
    elif k == 1:
        shape_kind, reverse_order = 'row', True
    elif k == 2:
        shape_kind, reverse_order = 'col', True
    else:
        shape_kind, reverse_order = 'row', False
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('SHAPE_KIND = %r' % shape_kind)
    lines.append('REVERSE_ORDER = %r' % reverse_order)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    vals, cnts = np.unique(g[g != BG], return_counts=True)')
    lines.append('    order = sorted(zip(cnts.tolist(), vals.tolist()), key=lambda t: (-t[0], t[1]))')
    lines.append('    if not order:')
    lines.append('        return [[BG]]')
    lines.append('    # The most frequent non-background colour is the filler; the rest are listed by count.')
    lines.append('    minority = [int(v) for c, v in order[1:]]')
    lines.append('    if not minority:')
    lines.append('        minority = [int(order[0][1])]')
    lines.append('    seq = list(reversed(minority)) if REVERSE_ORDER else minority')
    lines.append('    if SHAPE_KIND == "col":')
    lines.append('        return [[v] for v in seq]')
    lines.append('    return [seq]')
    lines.append('')
    return '\n'.join(lines) + '\n'
