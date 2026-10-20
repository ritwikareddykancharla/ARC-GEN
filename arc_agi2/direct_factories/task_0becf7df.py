def build_program(d4, palette):
    h0, w0 = 100, 200
    def fwd(r, c):
        h, w = h0, w0
        if d4 >= 4:
            c = w - 1 - c
        for _ in range(d4 % 4):
            r, c = c, h - 1 - r
            h, w = w, h
        return r, c, h, w
    exprs = []
    for (r, c) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        vr, vc, H, W = fwd(r, c)
        re_ = str(vr) if vr < H // 2 else 'H-%d' % (H - vr)
        ce_ = str(vc) if vc < W // 2 else 'W-%d' % (W - vc)
        exprs.append('(%s, %s)' % (re_, ce_))
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    p00 = ' + exprs[0])
    lines.append('    p01 = ' + exprs[1])
    lines.append('    p10 = ' + exprs[2])
    lines.append('    p11 = ' + exprs[3])
    lines.append('    legend = [p00, p01, p10, p11]')
    lines.append('    canvas = np.ones((H, W), dtype=bool)')
    lines.append('    for (r, c) in legend:')
    lines.append('        canvas[r, c] = False')
    lines.append('    pairs = [(int(g[p00]), int(g[p01])), (int(g[p10]), int(g[p11]))]')
    lines.append('    for a, b in pairs:')
    lines.append('        ma = (g == a) & canvas')
    lines.append('        mb = (g == b) & canvas')
    lines.append('        out[ma] = b')
    lines.append('        out[mb] = a')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
