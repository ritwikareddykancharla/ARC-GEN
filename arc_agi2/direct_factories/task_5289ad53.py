def build_program(d4, palette):
    # Track where each original output slot (0..5, reading order on the native
    # 2x3 canvas) ends up after the D4 transform.
    idx = [[0, 1, 2], [3, 4, 5]]
    if d4 >= 4:
        idx = [list(reversed(r)) for r in idx]
    for _ in range(d4 % 4):
        idx = [list(r) for r in zip(*idx[::-1])]
    H = len(idx)
    W = len(idx[0])
    pos = {}
    for r in range(H):
        for c in range(W):
            pos[idx[r][c]] = (r, c)
    order = [pos[k] for k in range(6)]
    green = int(palette[3])
    red = int(palette[2])
    empty = int(palette[0])
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import Counter, deque')
    lines.append('')
    lines.append('GREEN = %d' % green)
    lines.append('RED = %d' % red)
    lines.append('EMPTY = %d' % empty)
    lines.append('OUT_H = %d' % H)
    lines.append('OUT_W = %d' % W)
    lines.append('# visible-coordinate fill order of the tally slots')
    lines.append('ORDER = %r' % (order,))
    lines.append('')
    lines.append('def _count_components(g, colour):')
    lines.append('    h, w = g.shape')
    lines.append('    seen = np.zeros((h, w), dtype=bool)')
    lines.append('    n = 0')
    lines.append('    for y in range(h):')
    lines.append('        for x in range(w):')
    lines.append('            if g[y, x] == colour and not seen[y, x]:')
    lines.append('                n += 1')
    lines.append('                seen[y, x] = True')
    lines.append('                q = deque([(y, x)])')
    lines.append('                while q:')
    lines.append('                    cy, cx = q.popleft()')
    lines.append('                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                        ny, nx = cy + dy, cx + dx')
    lines.append('                        if 0 <= ny < h and 0 <= nx < w and g[ny, nx] == colour and not seen[ny, nx]:')
    lines.append('                            seen[ny, nx] = True')
    lines.append('                            q.append((ny, nx))')
    lines.append('    return n')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.array(grid, dtype=int)')
    lines.append('    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])')
    lines.append('    n_green = _count_components(g, GREEN) if bg != GREEN else 0')
    lines.append('    n_red = _count_components(g, RED) if bg != RED else 0')
    lines.append('    out = [[EMPTY] * OUT_W for _ in range(OUT_H)]')
    lines.append('    k = 0')
    lines.append('    for _ in range(n_green):')
    lines.append('        if k < len(ORDER):')
    lines.append('            r, c = ORDER[k]')
    lines.append('            out[r][c] = GREEN')
    lines.append('            k += 1')
    lines.append('    for _ in range(n_red):')
    lines.append('        if k < len(ORDER):')
    lines.append('            r, c = ORDER[k]')
    lines.append('            out[r][c] = RED')
    lines.append('            k += 1')
    lines.append('    return out')
    return '\n'.join(lines) + '\n'
