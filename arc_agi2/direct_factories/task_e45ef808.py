def build_program(d4, palette):
    # Original geometry: terrain grows along DOWN = (+1, 0); the tie-break axis is RIGHT = (0, +1).
    # Map these vectors through the episode transform: optional row reversal, then d4%4 clockwise turns.
    down = (1, 0)
    right = (0, 1)
    if d4 >= 4:
        right = (0, -1)
    for _ in range(d4 % 4):
        down = (down[1], -down[0])
        right = (right[1], -right[0])
    vertical = down[0] != 0
    sign = right[1] if vertical else right[0]
    bg = int(palette[1])
    ter = int(palette[6])
    pk = int(palette[4])
    vl = int(palette[9])
    src = []
    src.append('import numpy as np')
    src.append('')
    src.append('BG = ' + str(bg))
    src.append('TER = ' + str(ter))
    src.append('PEAK = ' + str(pk))
    src.append('VALLEY = ' + str(vl))
    src.append('# True: terrain bars are visible columns; False: terrain bars are visible rows')
    src.append('VERTICAL = ' + repr(bool(vertical)))
    src.append('# +1: the original rightward direction is increasing bar index; -1: it is decreasing bar index')
    src.append('SIGN = ' + str(int(sign)))
    src.append('')
    src.append('def _bar(a, i):')
    src.append('    if VERTICAL:')
    src.append('        return a[:, i]')
    src.append('    return a[i, :]')
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = np.array(grid, dtype=int)')
    src.append('    out = g.copy()')
    src.append('    n = g.shape[1] if VERTICAL else g.shape[0]')
    src.append('    heights = [int(np.count_nonzero(_bar(g, i) == TER)) for i in range(n)]')
    src.append('    # Tallest bar; a tie goes to the bar furthest along the original rightward direction.')
    src.append('    peak = max(range(n), key=lambda i: (heights[i], SIGN * i))')
    src.append('    # Shortest bar; a tie goes to the bar furthest along the original leftward direction.')
    src.append('    valley = min(range(n), key=lambda i: (heights[i], SIGN * i))')
    src.append('    for i, colour in ((peak, PEAK), (valley, VALLEY)):')
    src.append('        view = _bar(out, i)')
    src.append('        view[_bar(g, i) == BG] = colour')
    src.append('    return out.tolist()')
    return '\n'.join(src) + '\n'
