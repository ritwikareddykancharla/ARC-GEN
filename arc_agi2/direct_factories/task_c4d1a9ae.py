def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    flip = d4 >= 4
    # Original mechanism: bands are vertical (columns); each band takes the colour of the
    # next band in the +x (rightward) direction, cyclically.
    # Track that direction vector (dr, dc) through the D4 transform: optional row-reversal
    # (negates dc), then k clockwise rotations, each mapping (dr, dc) -> (dc, -dr).
    dr, dc = 0, (-1 if flip else 1)
    for _ in range(k):
        dr, dc = dc, -dr
    if dr == 0:
        axis = 'col'
        step = dc
    else:
        axis = 'row'
        step = dr
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter')
    lines.append('')
    lines.append('# Bands are runs of non-background ' + ('columns' if axis == 'col' else 'rows') + ' in the visible grid.')
    lines.append('# Each band recolours its background cells with the colour of the next band ' + ({('col', 1): 'to the right', ('col', -1): 'to the left', ('row', 1): 'below', ('row', -1): 'above'}[(axis, step)]) + ', cyclically.')
    lines.append('BAND_AXIS = ' + repr(axis))
    lines.append('STEP = ' + repr(step))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    cnt = Counter(g.ravel().tolist())')
    lines.append('    bg = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))[0]')
    lines.append('    if BAND_AXIS == "col":')
    lines.append('        L = W')
    lines.append('        sep = [bool(np.all(g[:, i] == bg)) for i in range(W)]')
    lines.append('    else:')
    lines.append('        L = H')
    lines.append('        sep = [bool(np.all(g[i, :] == bg)) for i in range(H)]')
    lines.append('    bands = []')
    lines.append('    i = 0')
    lines.append('    while i < L:')
    lines.append('        if sep[i]:')
    lines.append('            i += 1')
    lines.append('            continue')
    lines.append('        s = i')
    lines.append('        while i < L and not sep[i]:')
    lines.append('            i += 1')
    lines.append('        bands.append((s, i))')
    lines.append('    n = len(bands)')
    lines.append('    out = g.copy()')
    lines.append('    if n == 0:')
    lines.append('        return out.tolist()')
    lines.append('    cols = []')
    lines.append('    for s, e in bands:')
    lines.append('        sub = g[:, s:e] if BAND_AXIS == "col" else g[s:e, :]')
    lines.append('        vals = [int(v) for v in sub.ravel().tolist() if v != bg]')
    lines.append('        c = Counter(vals)')
    lines.append('        cols.append(max(c.items(), key=lambda kv: (kv[1], -kv[0]))[0])')
    lines.append('    for j, (s, e) in enumerate(bands):')
    lines.append('        c = cols[(j + STEP) % n]')
    lines.append('        if BAND_AXIS == "col":')
    lines.append('            sub = out[:, s:e]')
    lines.append('        else:')
    lines.append('            sub = out[s:e, :]')
    lines.append('        sub[sub == bg] = c')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
