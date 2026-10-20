def build_program(d4, palette):
    k = int(d4) % 4
    # Original mechanism: the shape colours slide along the ROW axis (vertically) so their top edge (min row) matches the anchor's.
    # The horizontal flip (d4>=4) only reverses columns, so the row axis is unaffected by it.
    # Clockwise rotation maps (r,c)->(c,H-1-r). So:
    #   k=0: rows, min;  k=1: columns, max;  k=2: rows, max;  k=3: columns, min.
    axis = 0 if k in (0, 2) else 1
    use_max = k in (1, 2)
    bg = int(palette[0])
    anchor = int(palette[1])
    movers = [int(palette[2]), int(palette[4])]
    lines = []
    lines.append('import numpy as np')
    lines.append('BG = ' + repr(bg))
    lines.append('ANCHOR = ' + repr(anchor))
    lines.append('MOVERS = ' + repr(movers))
    lines.append('AXIS = ' + repr(axis))
    lines.append('USE_MAX = ' + repr(use_max))
    lines.append('')
    lines.append('def _edge(coords):')
    lines.append('    return int(coords.max()) if USE_MAX else int(coords.min())')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    H, W = g.shape')
    lines.append('    apos = np.where(g == ANCHOR)')
    lines.append('    if len(apos[0]) == 0:')
    lines.append('        return out.tolist()')
    lines.append('    target = _edge(apos[AXIS])')
    lines.append('    present = [int(c) for c in np.unique(g) if int(c) != BG and int(c) != ANCHOR]')
    lines.append('    colours = [c for c in MOVERS if c in present] + [c for c in present if c not in MOVERS]')
    lines.append('    for c in colours:')
    lines.append('        ys, xs = np.where(g == c)')
    lines.append('        if len(ys) == 0:')
    lines.append('            continue')
    lines.append('        if AXIS == 0:')
    lines.append('            shift = target - _edge(ys)')
    lines.append('            ny = ys + shift')
    lines.append('            nx = xs')
    lines.append('        else:')
    lines.append('            shift = target - _edge(xs)')
    lines.append('            ny = ys')
    lines.append('            nx = xs + shift')
    lines.append('        out[ys, xs] = BG')
    lines.append('        valid = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)')
    lines.append('        out[ny[valid], nx[valid]] = c')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
