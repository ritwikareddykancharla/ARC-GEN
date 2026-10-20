def build_program(d4, palette):
    order = ['top', 'right', 'bottom', 'left']

    def image(edge):
        if d4 >= 4:
            if edge == 'left':
                edge = 'right'
            elif edge == 'right':
                edge = 'left'
        for _ in range(d4 % 4):
            edge = order[(order.index(edge) + 1) % 4]
        return edge

    hline_edge = image('top')
    vline_edge = image('right')
    bg = int(palette[0])

    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = ' + repr(bg))
    lines.append('EDGES = (' + repr(hline_edge) + ', ' + repr(vline_edge) + ')')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    border = set(g[0, :].tolist()) | set(g[-1, :].tolist()) | set(g[:, 0].tolist()) | set(g[:, -1].tolist())')
    lines.append('    colours = sorted(set(np.unique(g).tolist()) - {BG})')
    lines.append('    line_cands = [c for c in colours if c in border]')
    lines.append('    frame_cands = [c for c in colours if c not in border]')
    lines.append('    if not line_cands or not frame_cands:')
    lines.append('        return g.tolist()')
    lines.append('    line_c = line_cands[0]')
    lines.append('    frame_c = frame_cands[0]')
    lines.append('    ys, xs = np.nonzero(g == frame_c)')
    lines.append('    y0, y1 = int(ys.min()), int(ys.max())')
    lines.append('    x0, x1 = int(xs.min()), int(xs.max())')
    lines.append('    out = g.copy()')
    lines.append('    out[out == line_c] = BG')
    lines.append('    for edge in EDGES:')
    lines.append('        if edge == "top" or edge == "bottom":')
    lines.append('            r = y0 if edge == "top" else y1')
    lines.append('            for x in range(W):')
    lines.append('                if x < x0 or x > x1:')
    lines.append('                    out[r, x] = line_c')
    lines.append('        else:')
    lines.append('            c = x0 if edge == "left" else x1')
    lines.append('            for y in range(H):')
    lines.append('                if y < y0 or y > y1:')
    lines.append('                    out[y, c] = line_c')
    lines.append('    return out.tolist()')
    lines.append('')
    return '\n'.join(lines)
