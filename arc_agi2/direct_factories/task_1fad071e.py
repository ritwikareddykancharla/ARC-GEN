def build_program(d4, palette):
    d4 = int(d4) % 8
    BG = int(palette[0])
    BLUE = int(palette[1])
    H, W = 1, 5
    order = [(0, c) for c in range(5)]
    if d4 >= 4:
        order = [(r, W - 1 - c) for (r, c) in order]
    for _ in range(d4 % 4):
        order = [(c, H - 1 - r) for (r, c) in order]
        H, W = W, H
    src = []
    src.append('import numpy as np')
    src.append('from collections import deque')
    src.append('')
    src.append('BG = %d' % BG)
    src.append('BLUE = %d' % BLUE)
    src.append('OUT_H = %d' % H)
    src.append('OUT_W = %d' % W)
    src.append('FILL_ORDER = %r' % (order,))
    src.append('')
    src.append('def _count_blue_squares(g):')
    src.append('    h, w = g.shape')
    src.append('    seen = np.zeros((h, w), dtype=bool)')
    src.append('    count = 0')
    src.append('    for y in range(h):')
    src.append('        for x in range(w):')
    src.append('            if g[y, x] != BLUE or seen[y, x]:')
    src.append('                continue')
    src.append('            seen[y, x] = True')
    src.append('            q = deque([(y, x)])')
    src.append('            cells = []')
    src.append('            while q:')
    src.append('                cy, cx = q.popleft()')
    src.append('                cells.append((cy, cx))')
    src.append('                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    src.append('                    ny, nx = cy + dy, cx + dx')
    src.append('                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == BLUE:')
    src.append('                        seen[ny, nx] = True')
    src.append('                        q.append((ny, nx))')
    src.append('            if len(cells) == 4:')
    src.append('                ys = [c[0] for c in cells]')
    src.append('                xs = [c[1] for c in cells]')
    src.append('                if max(ys) - min(ys) == 1 and max(xs) - min(xs) == 1:')
    src.append('                    count += 1')
    src.append('    return count')
    src.append('')
    src.append('def solve(demonstrations, grid):')
    src.append('    g = np.asarray(grid, dtype=int)')
    src.append('    n = min(_count_blue_squares(g), len(FILL_ORDER))')
    src.append('    out = [[BG for _ in range(OUT_W)] for _ in range(OUT_H)]')
    src.append('    for i in range(n):')
    src.append('        r, c = FILL_ORDER[i]')
    src.append('        out[r][c] = BLUE')
    src.append('    return out')
    return '\n'.join(src) + '\n'
