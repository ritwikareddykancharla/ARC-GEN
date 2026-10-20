def build_program(d4, palette):
    d4 = int(d4)

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    down = tf((1, 0))
    right = tf((0, 1))
    up = (-down[0], -down[1])
    ray_a = (up[0] - right[0], up[1] - right[1])
    ray_b = (up[0] + right[0], up[1] + right[1])
    bg = int(palette[0])
    line = int(palette[2])
    pix = int(palette[4])
    lines = []
    lines.append('import numpy as np')
    lines.append('BG = ' + repr(bg))
    lines.append('LINE = ' + repr(line))
    lines.append('PIX = ' + repr(pix))
    lines.append('DR, DC = ' + repr(down))
    lines.append('RAYS = ' + repr((ray_a, ray_b)))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    pts = [(int(r), int(c)) for r, c in zip(*np.nonzero(g == PIX))]')
    lines.append('    for r, c in pts:')
    lines.append('        out[r, c] = BG')
    lines.append('    landed = []')
    lines.append('    for r, c in pts:')
    lines.append('        nr, nc = r + DR, c + DC')
    lines.append('        if 0 <= nr < H and 0 <= nc < W and g[nr, nc] != LINE:')
    lines.append('            out[nr, nc] = PIX')
    lines.append('            br, bc = nr + DR, nc + DC')
    lines.append('            if 0 <= br < H and 0 <= bc < W and g[br, bc] == LINE:')
    lines.append('                landed.append((nr, nc))')
    lines.append('        else:')
    lines.append('            out[r, c] = PIX')
    lines.append('    for r, c in landed:')
    lines.append('        for ar, ac in RAYS:')
    lines.append('            y, x = r + ar, c + ac')
    lines.append('            while 0 <= y < H and 0 <= x < W:')
    lines.append('                out[y, x] = PIX')
    lines.append('                y += ar')
    lines.append('                x += ac')
    lines.append('    return [[int(v) for v in row] for row in out.tolist()]')
    return '\n'.join(lines) + '\n'
