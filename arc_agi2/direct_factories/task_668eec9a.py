def build_program(d4, palette):
    k = int(d4) % 8
    # Track how each visible axis is expressed in terms of original axes.
    # Each entry is (original_axis, reversed_flag).
    vrow = ('r', False)
    vcol = ('c', False)
    if k >= 4:
        vcol = (vcol[0], not vcol[1])
    for _ in range(k % 4):
        # clockwise rotation: (r, c) in HxW -> (c, H-1-r)
        vrow, vcol = vcol, (vrow[0], not vrow[1])

    def expr(axis):
        if vrow[0] == axis:
            kind, rev = 'row', vrow[1]
        else:
            kind, rev = 'col', vcol[1]
        var = 'ys' if kind == 'row' else 'xs'
        if rev:
            return '-int(%s.max())' % var
        return 'int(%s.min())' % var

    primary = expr('r')
    secondary = expr('c')
    transposed = vrow[0] != 'r'
    if transposed:
        oh, ow = 3, 5
        band_rev = vcol[1]
    else:
        oh, ow = 5, 3
        band_rev = vrow[1]

    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('')
    lines.append('OUT_H = %d' % oh)
    lines.append('OUT_W = %d' % ow)
    lines.append('BANDS = 5')
    lines.append('BAND_REV = %s' % ('True' if band_rev else 'False'))
    lines.append('BANDS_ARE_COLUMNS = %s' % ('True' if transposed else 'False'))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])')
    lines.append('    info = []')
    lines.append('    for c in sorted(set(g.ravel().tolist())):')
    lines.append('        if c == bg:')
    lines.append('            continue')
    lines.append('        ys, xs = np.nonzero(g == c)')
    lines.append('        a = ' + primary)
    lines.append('        b = ' + secondary)
    lines.append('        info.append((a, b, int(c)))')
    lines.append('    info.sort()')
    lines.append('    out = np.full((OUT_H, OUT_W), bg, dtype=int)')
    lines.append('    start = BANDS - len(info)')
    lines.append('    for i, (_, _, c) in enumerate(info):')
    lines.append('        r = start + i')
    lines.append('        if 0 <= r < BANDS:')
    lines.append('            p = (BANDS - 1 - r) if BAND_REV else r')
    lines.append('            if BANDS_ARE_COLUMNS:')
    lines.append('                out[:, p] = c')
    lines.append('            else:')
    lines.append('                out[p, :] = c')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
