def build_program(d4, palette):
    k = int(d4) % 4
    # Native rule: vertical segments are drawn over horizontal ones.
    # Reversing each row (d4>=4) keeps vertical lines vertical.
    # Each clockwise rotation swaps the two axes, so an odd rotation count
    # makes the visible horizontal segments the ones drawn on top.
    top_vertical = (k % 2 == 0)
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('TOP_VERTICAL = %s' % ('True' if top_vertical else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    horiz = []')
    lines.append('    vert = []')
    lines.append('    for c in sorted(set(int(v) for v in np.unique(g))):')
    lines.append('        if c == BG:')
    lines.append('            continue')
    lines.append('        ys, xs = np.where(g == c)')
    lines.append('        if len(ys) != 2:')
    lines.append('            continue')
    lines.append('        y0, x0, y1, x1 = int(ys[0]), int(xs[0]), int(ys[1]), int(xs[1])')
    lines.append('        if y0 == y1:')
    lines.append('            horiz.append((c, y0, min(x0, x1), max(x0, x1)))')
    lines.append('        elif x0 == x1:')
    lines.append('            vert.append((c, x0, min(y0, y1), max(y0, y1)))')
    lines.append('    def draw_h():')
    lines.append('        for c, y, xa, xb in horiz:')
    lines.append('            out[y, xa:xb + 1] = c')
    lines.append('    def draw_v():')
    lines.append('        for c, x, ya, yb in vert:')
    lines.append('            out[ya:yb + 1, x] = c')
    lines.append('    if TOP_VERTICAL:')
    lines.append('        draw_h()')
    lines.append('        draw_v()')
    lines.append('    else:')
    lines.append('        draw_v()')
    lines.append('        draw_h()')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
