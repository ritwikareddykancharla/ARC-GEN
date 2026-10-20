def build_program(d4, palette):
    bg = int(palette[7])
    br = int(palette[4])
    rot = int(d4) % 4
    head = [
        'BG = ' + str(bg),
        'BR = ' + str(br),
        '',
        'def solve(demonstrations, grid):',
        '    g = [[int(v) for v in row] for row in grid]',
        '    H = len(g)',
        '    W = len(g[0]) if H else 0',
        '    out = [row[:] for row in g]',
        '    cells = [(r, c, g[r][c]) for r in range(H) for c in range(W) if g[r][c] != BG and g[r][c] != BR]',
        '    if not cells:',
        '        return out',
        '    rs = [r for r, c, v in cells]',
        '    cs = [c for r, c, v in cells]',
    ]
    if rot == 0:
        block = [
            '    # object falls downward; source cup hangs from the top row',
            '    edge = [c for c in range(W) if g[0][c] == BR]',
            '    if not edge:',
            '        return out',
            '    span = max(edge) - min(edge) + 1',
            '    size = max(cs) - min(cs) + 1',
            '    dc = min(edge) + (span - size) // 2 - min(cs)',
            '    dr = (H - 1) - max(rs)',
        ]
    elif rot == 2:
        block = [
            '    # object falls upward; source cup stands on the bottom row',
            '    edge = [c for c in range(W) if g[H - 1][c] == BR]',
            '    if not edge:',
            '        return out',
            '    span = max(edge) - min(edge) + 1',
            '    size = max(cs) - min(cs) + 1',
            '    dc = min(edge) + (span - size) // 2 - min(cs)',
            '    dr = 0 - min(rs)',
        ]
    elif rot == 1:
        block = [
            '    # object moves left; source cup is attached to the right column',
            '    edge = [r for r in range(H) if g[r][W - 1] == BR]',
            '    if not edge:',
            '        return out',
            '    span = max(edge) - min(edge) + 1',
            '    size = max(rs) - min(rs) + 1',
            '    dr = min(edge) + (span - size) // 2 - min(rs)',
            '    dc = 0 - min(cs)',
        ]
    else:
        block = [
            '    # object moves right; source cup is attached to the left column',
            '    edge = [r for r in range(H) if g[r][0] == BR]',
            '    if not edge:',
            '        return out',
            '    span = max(edge) - min(edge) + 1',
            '    size = max(rs) - min(rs) + 1',
            '    dr = min(edge) + (span - size) // 2 - min(rs)',
            '    dc = (W - 1) - max(cs)',
        ]
    tail = [
        '    for r, c, v in cells:',
        '        out[r][c] = BG',
        '    for r, c, v in cells:',
        '        nr = r + dr',
        '        nc = c + dc',
        '        if 0 <= nr < H and 0 <= nc < W:',
        '            out[nr][nc] = v',
        '    return out',
    ]
    return '\n'.join(head + block + tail) + '\n'
