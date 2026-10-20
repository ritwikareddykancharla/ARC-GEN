def build_program(d4, palette):
    d4 = int(d4)

    def tf(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (int(dr), int(dc))

    A = tf((-1, 0))
    B = tf((0, 1))
    bg = int(palette[0])
    fill = int(palette[5])
    lines = [
        'import numpy as np',
        '',
        'A = (%d, %d)' % A,
        'B = (%d, %d)' % B,
        'BG = %d' % bg,
        'FILL = %d' % fill,
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    out = g.copy()',
        '    seeds = [(int(y), int(x)) for y, x in zip(*np.nonzero(g != BG))]',
        '    for r, c in seeds:',
        '        for s in (1, -1):',
        '            a = (s * A[0], s * A[1])',
        '            b = (s * B[0], s * B[1])',
        '            moves = [a, a, b, b]',
        '            y, x, k = r, c, 0',
        '            while True:',
        '                dy, dx = moves[k % 4]',
        '                y += dy',
        '                x += dx',
        '                k += 1',
        '                if not (0 <= y < H and 0 <= x < W):',
        '                    break',
        '                if out[y, x] == BG:',
        '                    out[y, x] = FILL',
        '    return out.tolist()',
        '',
    ]
    return '\n'.join(lines)
