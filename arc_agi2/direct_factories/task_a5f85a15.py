def build_program(d4, palette):
    # Original mechanism: each diagonal line runs along step (+1,+1) from its upper-left end.
    # Cells at odd step indices become yellow (4). Map that step vector into visible coordinates.
    dr, dc = 1, 1
    if d4 >= 4:
        # reverse each row: column direction flips
        dc = -dc
    for _ in range(d4 % 4):
        # clockwise rotation: (r, c) -> (c, n-1-r), so direction (dr, dc) -> (dc, -dr)
        dr, dc = dc, -dr
    bg = int(palette[0])
    mark = int(palette[4])
    lines = []
    lines.append('import numpy as np')
    lines.append('')
    lines.append('BG = ' + str(bg))
    lines.append('MARK = ' + str(mark))
    lines.append('DR = ' + str(dr))
    lines.append('DC = ' + str(dc))
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    H, W = g.shape')
    lines.append('    out = g.copy()')
    lines.append('    for y in range(H):')
    lines.append('        for x in range(W):')
    lines.append('            if g[y, x] == BG:')
    lines.append('                continue')
    lines.append('            py, px = y - DR, x - DC')
    lines.append('            if 0 <= py < H and 0 <= px < W and g[py, px] != BG:')
    lines.append('                continue')
    lines.append('            i = 0')
    lines.append('            cy, cx = y, x')
    lines.append('            while 0 <= cy < H and 0 <= cx < W and g[cy, cx] != BG:')
    lines.append('                if i % 2 == 1:')
    lines.append('                    out[cy, cx] = MARK')
    lines.append('                i += 1')
    lines.append('                cy += DR')
    lines.append('                cx += DC')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
