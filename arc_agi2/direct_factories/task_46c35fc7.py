def build_program(d4, palette):
    base = {(0, 0): (0, 2), (0, 2): (2, 2), (2, 2): (2, 0), (2, 0): (0, 0),
            (0, 1): (1, 0), (1, 2): (0, 1), (2, 1): (1, 2), (1, 0): (2, 1)}

    def tf(p):
        r, c = p
        if d4 >= 4:
            c = 2 - c
        for _ in range(d4 % 4):
            r, c = c, 2 - r
        return (r, c)

    mp = {}
    for d, s in base.items():
        mp[tf(d)] = tf(s)
    items = sorted(mp.items())
    bg = int(palette[7])
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import deque')
    lines.append('')
    lines.append('BG = ' + repr(bg))
    lines.append('RING_MAP = ' + repr(items))
    lines.append('')
    lines.append('def _components(mask):')
    lines.append('    h, w = mask.shape')
    lines.append('    seen = np.zeros_like(mask, bool)')
    lines.append('    out = []')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if mask[y, x] and not seen[y, x]:')
    lines.append('                q = deque([(y, x)])')
    lines.append('                seen[y, x] = True')
    lines.append('                cells = []')
    lines.append('                while q:')
    lines.append('                    cy, cx = q.popleft()')
    lines.append('                    cells.append((cy, cx))')
    lines.append('                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                        ny, nx = cy + dy, cx + dx')
    lines.append('                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:')
    lines.append('                            seen[ny, nx] = True')
    lines.append('                            q.append((ny, nx))')
    lines.append('                out.append(cells)')
    lines.append('    return out')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    out = g.copy()')
    lines.append('    for comp in _components(g != BG):')
    lines.append('        ys = [p[0] for p in comp]')
    lines.append('        xs = [p[1] for p in comp]')
    lines.append('        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)')
    lines.append('        if y1 - y0 != 2 or x1 - x0 != 2:')
    lines.append('            continue')
    lines.append('        for (dy, dx), (sy, sx) in RING_MAP:')
    lines.append('            out[y0 + dy, x0 + dx] = g[y0 + sy, x0 + sx]')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
