def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    gray = int(palette[5])
    # Original marker row is the top row, and alignment is by column (x).
    # A horizontal flip (d4>=4) keeps the top row on top and keeps the column axis.
    # Each clockwise rotation moves the marker edge top->right->bottom->left
    # and swaps the alignment axis.
    if k == 0:
        line = '[(0, x) for x in range(W)]'
        ax = 1
    elif k == 1:
        line = '[(y, W - 1) for y in range(H)]'
        ax = 0
    elif k == 2:
        line = '[(H - 1, x) for x in range(W)]'
        ax = 1
    else:
        line = '[(y, 0) for y in range(H)]'
        ax = 0
    lines = [
        'import numpy as np',
        'from collections import deque',
        '',
        'BG = %d' % bg,
        'GRAY = %d' % gray,
        'AX = %d  # 1: markers aligned by column (x); 0: by row (y)' % ax,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = g.copy()',
        '    markers = []',
        '    for (y, x) in ' + line + ':',
        '        v = int(g[y, x])',
        '        if v != BG and v != GRAY:',
        '            markers.append(((y, x)[AX], v))',
        '    if not markers:',
        '        return out.tolist()',
        '    seen = np.zeros((H, W), dtype=bool)',
        '    for sy in range(H):',
        '        for sx in range(W):',
        '            if g[sy, sx] != GRAY or seen[sy, sx]:',
        '                continue',
        '            seen[sy, sx] = True',
        '            q = deque([(sy, sx)])',
        '            cells = []',
        '            while q:',
        '                cy, cx = q.popleft()',
        '                cells.append((cy, cx))',
        '                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):',
        '                    ny, nx = cy + dy, cx + dx',
        '                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == GRAY:',
        '                        seen[ny, nx] = True',
        '                        q.append((ny, nx))',
        '            coords = [c[AX] for c in cells]',
        '            lo, hi = min(coords), max(coords)',
        '            inside = [m for m in markers if lo <= m[0] <= hi]',
        '            if inside:',
        '                colour = inside[0][1]',
        '            else:',
        '                mid = (lo + hi) / 2.0',
        '                colour = min(markers, key=lambda m: (abs(m[0] - mid), m[0]))[1]',
        '            for cy, cx in cells:',
        '                out[cy, cx] = colour',
        '    return out.tolist()',
    ]
    return '\n'.join(lines) + '\n'
