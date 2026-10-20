def build_program(d4, palette):
    base_dirs = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dirs = []
    for dr, dc in base_dirs:
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        dirs.append((int(dr), int(dc)))
    bg = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('DIRS = ' + repr(dirs))
    lines.append('BG = ' + repr(bg))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    h, w = g.shape')
    lines.append('    H, W = 3 * h, 3 * w')
    lines.append('    out = np.full((H, W), BG, dtype=int)')
    lines.append('    ys, xs = np.nonzero(g != BG)')
    lines.append('    if len(ys) == 0:')
    lines.append('        return out.tolist()')
    lines.append('    y, x = int(ys[0]), int(xs[0])')
    lines.append('    c = int(g[y, x])')
    lines.append('    ay = y * (H - 1) // (h - 1) if h > 1 else (H - 1) // 2')
    lines.append('    ax = x * (W - 1) // (w - 1) if w > 1 else (W - 1) // 2')
    lines.append('    r, q = ay, ax')
    lines.append('    length = 2')
    lines.append('    nseg = max(20, 4 * (max(H, W) // 2 + 2))')
    lines.append('    for i in range(nseg):')
    lines.append('        dr, dq = DIRS[i % 4]')
    lines.append('        for _ in range(length):')
    lines.append('            if 0 <= r < H and 0 <= q < W:')
    lines.append('                out[r, q] = c')
    lines.append('            r += dr')
    lines.append('            q += dq')
    lines.append('        if i % 4 in (1, 3):')
    lines.append('            length += 2')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
