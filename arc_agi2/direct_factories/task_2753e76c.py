def build_program(d4, palette):
    d4 = int(d4) % 8
    bg = int(palette[0])
    # (horizontal_bars, anchor_at_end, largest_first) in visible coordinates
    table = {
        0: (True, True, True),
        1: (False, True, False),
        2: (True, False, False),
        3: (False, False, True),
        4: (True, False, True),
        5: (False, False, False),
        6: (True, True, False),
        7: (False, True, True),
    }
    horiz, anchor_end, largest_first = table[d4]
    lines = []
    lines.append('import numpy as np')
    lines.append('from collections import deque')
    lines.append('')
    lines.append('BG = %d' % bg)
    lines.append('HORIZONTAL = %s' % ('True' if horiz else 'False'))
    lines.append('ANCHOR_END = %s' % ('True' if anchor_end else 'False'))
    lines.append('LARGEST_FIRST = %s' % ('True' if largest_first else 'False'))
    lines.append('')
    lines.append('def _count_objects(g):')
    lines.append('    H, W = g.shape')
    lines.append('    seen = np.zeros((H, W), dtype=bool)')
    lines.append('    counts = {}')
    lines.append('    for y in range(H):')
    lines.append('        for x in range(W):')
    lines.append('            c = int(g[y, x])')
    lines.append('            if c == BG or seen[y, x]:')
    lines.append('                continue')
    lines.append('            seen[y, x] = True')
    lines.append('            q = deque([(y, x)])')
    lines.append('            while q:')
    lines.append('                cy, cx = q.popleft()')
    lines.append('                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):')
    lines.append('                    ny, nx = cy + dy, cx + dx')
    lines.append('                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and int(g[ny, nx]) == c:')
    lines.append('                        seen[ny, nx] = True')
    lines.append('                        q.append((ny, nx))')
    lines.append('            counts[c] = counts.get(c, 0) + 1')
    lines.append('    return counts')
    lines.append('')
    lines.append('def solve(demonstrations, grid):')
    lines.append('    g = np.asarray(grid, dtype=int)')
    lines.append('    counts = _count_objects(g)')
    lines.append('    if not counts:')
    lines.append('        return [[BG]]')
    lines.append('    order = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))')
    lines.append('    n = len(order)')
    lines.append('    L = max(cnt for _, cnt in order)')
    lines.append('    if HORIZONTAL:')
    lines.append('        out = np.full((n, L), BG, dtype=int)')
    lines.append('    else:')
    lines.append('        out = np.full((L, n), BG, dtype=int)')
    lines.append('    for rank, (col, cnt) in enumerate(order):')
    lines.append('        i = rank if LARGEST_FIRST else n - 1 - rank')
    lines.append('        if HORIZONTAL:')
    lines.append('            if ANCHOR_END:')
    lines.append('                out[i, L - cnt:] = col')
    lines.append('            else:')
    lines.append('                out[i, :cnt] = col')
    lines.append('        else:')
    lines.append('            if ANCHOR_END:')
    lines.append('                out[L - cnt:, i] = col')
    lines.append('            else:')
    lines.append('                out[:cnt, i] = col')
    lines.append('    return out.tolist()')
    return '\n'.join(lines) + '\n'
