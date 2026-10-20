def build_program(d4, palette):
    d4 = int(d4) % 8

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    # Canonical fill (most frequent colour first): inner step upward (-1,0),
    # outer step rightward (0,1), starting bottom-left.
    fill_inner = tf((-1, 0))
    fill_outer = tf((0, 1))
    # Canonical tie-break scan: row-major, inner step right (0,1), outer step down (1,0).
    scan_inner = tf((0, 1))
    scan_outer = tf((1, 0))

    def loop(inner, outer):
        if inner[0] != 0:
            rows = 'range(H)' if inner[0] > 0 else 'range(H - 1, -1, -1)'
            cols = 'range(W)' if outer[1] > 0 else 'range(W - 1, -1, -1)'
            return '[(r, c) for c in ' + cols + ' for r in ' + rows + ']'
        cols = 'range(W)' if inner[1] > 0 else 'range(W - 1, -1, -1)'
        rows = 'range(H)' if outer[0] > 0 else 'range(H - 1, -1, -1)'
        return '[(r, c) for r in ' + rows + ' for c in ' + cols + ']'

    lines = [
        'def solve(demonstrations, grid):',
        '    H = len(grid)',
        '    W = len(grid[0]) if H else 0',
        '    # visible scan order used to rank tied colours by first appearance',
        '    scan = ' + loop(scan_inner, scan_outer),
        '    counts = {}',
        '    first = {}',
        '    for k, (r, c) in enumerate(scan):',
        '        v = grid[r][c]',
        '        if v not in counts:',
        '            counts[v] = 0',
        '            first[v] = k',
        '        counts[v] += 1',
        '    order = sorted(counts, key=lambda v: (-counts[v], first[v]))',
        '    # visible fill path: most frequent colour laid first, rarest ends at the far corner',
        '    fill = ' + loop(fill_inner, fill_outer),
        '    out = [[0] * W for _ in range(H)]',
        '    i = 0',
        '    for v in order:',
        '        for _ in range(counts[v]):',
        '            r, c = fill[i]',
        '            out[r][c] = v',
        '            i += 1',
        '    return out',
    ]
    return '\n'.join(lines) + '\n'
