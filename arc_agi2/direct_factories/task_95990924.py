def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    corner_map = {}
    for dr in (0, 1):
        for dc in (0, 1):
            vy, vx = 2 * dr - 1, 2 * dc - 1
            colour = 2 * dr + dc + 1
            if d4 >= 4:
                vx = -vx
            for _ in range(d4 % 4):
                vy, vx = vx, -vy
            corner_map[(vy, vx)] = pal[colour]
    corners = sorted(corner_map.items())
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import deque')
    lines.append('')
    lines.append('BG = %d' % pal[0])
    lines.append('SQ = %d' % pal[5])
    lines.append('CORNERS = %r' % [(k[0], k[1], v) for k, v in corners])
    lines.append('')
    lines.append('def _components(mask):')
    lines.append('    h, w = mask.shape')
    lines.append('    seen = np.zeros_like(mask, dtype=bool)')
    lines.append('    out = []')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if mask[y, x] and not seen[y, x]:')
    lines.append('                seen[y, x] = True')
    lines.append('                q = deque([(y, x)])')
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
    lines.append('    H, W = g.shape')
    lines.append('    comps = _components(g == SQ)')
    lines.append('    for cells in comps:')
    lines.append('        ys = [c[0] for c in cells]')
    lines.append('        xs = [c[1] for c in cells]')
    lines.append('        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)')
    lines.append('        for vy, vx, col in CORNERS:')
    lines.append('            y = y0 - 1 if vy < 0 else y1 + 1')
    lines.append('            x = x0 - 1 if vx < 0 else x1 + 1')
    lines.append('            if 0 <= y < H and 0 <= x < W and out[y, x] == BG:')
    lines.append('                out[y, x] = col')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
