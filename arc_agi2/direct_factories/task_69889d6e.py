def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(p) for p in palette]

    def tv(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    up = tv((-1, 0))
    rt = tv((0, 1))
    bg = pal[0]
    red = pal[2]
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('UP_R = %d' % up[0])
    lines.append('UP_C = %d' % up[1])
    lines.append('RT_R = %d' % rt[0])
    lines.append('RT_C = %d' % rt[1])
    lines.append('BG = %d' % bg)
    lines.append('RED = %d' % red)
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int).copy()')
    lines.append('    H, W = g.shape')
    lines.append('    pos = np.argwhere(g == RED)')
    lines.append('    if len(pos) == 0:')
    lines.append('        return g.tolist()')
    lines.append('    y, x = int(pos[0][0]), int(pos[0][1])')
    lines.append('    phase_up = True')
    lines.append('    steps = 0')
    lines.append('    limit = 4 * H * W + 8')
    lines.append('    while steps < limit:')
    lines.append('        steps += 1')
    lines.append('        if phase_up:')
    lines.append('            ny, nx = y + UP_R, x + UP_C')
    lines.append('            if not (0 <= ny < H and 0 <= nx < W):')
    lines.append('                break')
    lines.append('            if g[ny, nx] != BG:')
    lines.append('                sy, sx = y + RT_R, x + RT_C')
    lines.append('                if not (0 <= sy < H and 0 <= sx < W) or g[sy, sx] != BG:')
    lines.append('                    break')
    lines.append('                y, x = sy, sx')
    lines.append('                g[y, x] = RED')
    lines.append('                continue')
    lines.append('            y, x = ny, nx')
    lines.append('            g[y, x] = RED')
    lines.append('            phase_up = False')
    lines.append('        else:')
    lines.append('            sy, sx = y + RT_R, x + RT_C')
    lines.append('            if not (0 <= sy < H and 0 <= sx < W) or g[sy, sx] != BG:')
    lines.append('                break')
    lines.append('            y, x = sy, sx')
    lines.append('            g[y, x] = RED')
    lines.append('            phase_up = True')
    lines.append('    return g.tolist()')
    return '\n'.join(lines) + '\n'
