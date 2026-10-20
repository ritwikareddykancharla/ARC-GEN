def build_program(d4, palette):
    pal = [int(c) for c in palette]
    sep = pal[2]
    bg = pal[0]
    k = int(d4) % 4
    side = 'L' if int(d4) < 4 else 'R'
    cw = {'L': 'T', 'T': 'R', 'R': 'B', 'B': 'L'}
    for _ in range(k):
        side = cw[side]
    axis = 'cols' if side in ('L', 'R') else 'rows'
    from_start = side in ('L', 'T')
    lines = [
        'import numpy as np',
        '',
        'SEP = %d' % sep,
        'BG = %d' % bg,
        'AXIS = %r' % axis,
        'FROM_START = %r' % from_start,
        '',
        'def _panels(g):',
        '    H, W = g.shape',
        '    if AXIS == "cols":',
        '        cuts = [x for x in range(W) if np.all(g[:, x] == SEP)]',
        '        edges = [-1] + cuts + [W]',
        '        pans = [g[:, edges[i] + 1:edges[i + 1]] for i in range(len(edges) - 1) if edges[i + 1] - edges[i] > 1]',
        '    else:',
        '        cuts = [y for y in range(H) if np.all(g[y, :] == SEP)]',
        '        edges = [-1] + cuts + [H]',
        '        pans = [g[edges[i] + 1:edges[i + 1], :] for i in range(len(edges) - 1) if edges[i + 1] - edges[i] > 1]',
        '    return pans',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    pans = _panels(g)',
        '    if not pans:',
        '        return g.tolist()',
        '    if not FROM_START:',
        '        pans = pans[::-1]',
        '    h = min(p.shape[0] for p in pans)',
        '    w = min(p.shape[1] for p in pans)',
        '    out = np.full((h, w), BG, dtype=int)',
        '    for p in reversed(pans):',
        '        q = p[:h, :w]',
        '        m = q != BG',
        '        out[m] = q[m]',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
