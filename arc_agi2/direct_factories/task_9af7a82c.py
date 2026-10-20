def build_program(d4, palette):
    d = int(d4) % 8
    table = {
        0: ('v', False, False),
        1: ('h', True, False),
        2: ('v', True, True),
        3: ('h', False, True),
        4: ('v', False, True),
        5: ('h', True, True),
        6: ('v', True, False),
        7: ('h', False, False),
    }
    orient, anchor_end, largest_last = table[d]
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('ORIENT = %r' % orient)
    lines.append('ANCHOR_END = %r' % bool(anchor_end))
    lines.append('LARGEST_LAST = %r' % bool(largest_last))
    lines.append('BG = %d' % bg)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    order = []')
    lines.append('    for v in g.flatten():')
    lines.append('        v = int(v)')
    lines.append('        if v not in order:')
    lines.append('            order.append(v)')
    lines.append('    counts = {c: int((g == c).sum()) for c in order}')
    lines.append('    cols = sorted(order, key=lambda c: (-counts[c], order.index(c)))')
    lines.append('    h = counts[cols[0]]')
    lines.append('    k = len(cols)')
    lines.append('    if ORIENT == "v":')
    lines.append('        out = np.full((h, k), BG, dtype=int)')
    lines.append('    else:')
    lines.append('        out = np.full((k, h), BG, dtype=int)')
    lines.append('    for i, c in enumerate(cols):')
    lines.append('        slot = (k - 1 - i) if LARGEST_LAST else i')
    lines.append('        n = counts[c]')
    lines.append('        if ANCHOR_END:')
    lines.append('            lo, hi = h - n, h')
    lines.append('        else:')
    lines.append('            lo, hi = 0, n')
    lines.append('        if ORIENT == "v":')
    lines.append('            out[lo:hi, slot] = c')
    lines.append('        else:')
    lines.append('            out[slot, lo:hi] = c')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
