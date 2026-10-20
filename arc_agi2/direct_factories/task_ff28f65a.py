def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    fg = pal[1]
    obj = pal[2]

    def tf(r, c, n=3):
        if d4 >= 4:
            c = n - 1 - c
        for _ in range(d4 % 4):
            r, c = c, n - 1 - r
        return (r, c)

    base_order = [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]
    order = [tf(r, c) for (r, c) in base_order]

    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import deque')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('FG = %d' % fg)
    lines.append('OBJ = %d' % obj)
    lines.append('ORDER = %r' % (order,))
    lines.append('')
    lines.append('def _count_objects(g):')
    lines.append('    h, w = g.shape')
    lines.append('    mask = g != BG')
    lines.append('    seen = np.zeros_like(mask, dtype=bool)')
    lines.append('    count = 0')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if mask[y, x] and not seen[y, x]:')
    lines.append('                count += 1')
    lines.append('                seen[y, x] = True')
    lines.append('                q = deque([(y, x)])')
    lines.append('                col = g[y, x]')
    lines.append('                while q:')
    lines.append('                    cy, cx = q.popleft()')
    lines.append('                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                        ny, nx = cy + dy, cx + dx')
    lines.append('                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx] and g[ny, nx] == col:')
    lines.append('                            seen[ny, nx] = True')
    lines.append('                            q.append((ny, nx))')
    lines.append('    return count')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    n = _count_objects(g)')
    lines.append('    out = [[BG for _ in range(3)] for _ in range(3)]')
    lines.append('    for i, (r, c) in enumerate(ORDER):')
    lines.append('        if i >= n:')
    lines.append('            break')
    lines.append('        out[r][c] = FG')
    lines.append('    return out')
    lines.append('')
    return '\n'.join(lines)
