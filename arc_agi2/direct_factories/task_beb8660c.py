def build_program(d4, palette):
    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    down = tf((1, 0))
    right = tf((0, 1))
    bg = int(palette[0])
    L = [
        'import numpy as np',
        'from collections import deque',
        'BG = %d' % bg,
        '',
        'def _bars(g, mask):',
        '    H, W = g.shape',
        '    seen = np.zeros((H, W), bool)',
        '    bars = []',
        '    for y in range(H):',
        '        for x in range(W):',
        '            if (not mask[y, x]) or seen[y, x] or g[y, x] == BG:',
        '                continue',
        '            c = int(g[y, x])',
        '            q = deque([(y, x)])',
        '            seen[y, x] = True',
        '            n = 0',
        '            while q:',
        '                cy, cx = q.popleft()',
        '                n += 1',
        '                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):',
        '                    ny, nx = cy + dy, cx + dx',
        '                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and (not seen[ny, nx]) and g[ny, nx] == c:',
        '                        seen[ny, nx] = True',
        '                        q.append((ny, nx))',
        '            bars.append((n, c))',
        '    bars.sort(key=lambda b: -b[0])',
        '    return bars',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = np.full_like(g, BG)',
        '    mask = np.ones((H, W), bool)',
    ]
    if down[0] != 0:
        floor_end = down[0] > 0
        align_end = right[1] > 0
        L += [
            '    f = %s' % ('H - 1' if floor_end else '0'),
            '    out[f, :] = g[f, :]',
            '    mask[f, :] = False',
            '    bars = _bars(g, mask)',
            '    y = %s' % ('H - 2' if floor_end else '1'),
            '    for n, c in bars:',
            '        n = min(n, W)',
            '        if 0 <= y < H:',
            '            out[y, %s] = c' % ('W - n:W' if align_end else '0:n'),
            '        y += %d' % (-1 if floor_end else 1),
        ]
    else:
        floor_end = down[1] > 0
        align_end = right[0] > 0
        L += [
            '    f = %s' % ('W - 1' if floor_end else '0'),
            '    out[:, f] = g[:, f]',
            '    mask[:, f] = False',
            '    bars = _bars(g, mask)',
            '    x = %s' % ('W - 2' if floor_end else '1'),
            '    for n, c in bars:',
            '        n = min(n, H)',
            '        if 0 <= x < W:',
            '            out[%s, x] = c' % ('H - n:H' if align_end else '0:n'),
            '        x += %d' % (-1 if floor_end else 1),
        ]
    L.append('    return out.tolist()')
    return '\n'.join(L) + '\n'
