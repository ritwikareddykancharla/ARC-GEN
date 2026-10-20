def build_program(d4, palette):
    # Visible grids are 30x30. Index range is 0..n.
    n = 29
    # Native mirror: a <-> 31 - a (axes at 15.5), plus the transpose.
    A = 31

    def mul(P, Q):
        return [[sum(P[i][k] * Q[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    # F maps native (y, x) to visible (y, x) as an affine integer map.
    F = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    if d4 >= 4:
        F = mul([[1, 0, 0], [0, -1, n], [0, 0, 1]], F)
    rot = [[0, 1, 0], [-1, 0, n], [0, 0, 1]]
    for _ in range(d4 % 4):
        F = mul(rot, F)
    a, b, c, d = F[0][0], F[0][1], F[1][0], F[1][1]
    ty, tx = F[0][2], F[1][2]
    Finv = [[a, c, -(a * ty + c * tx)], [b, d, -(b * ty + d * tx)], [0, 0, 1]]

    # Native partner maps: mirrors first, then transpose-based ones.
    natives = [
        [[1, 0, 0], [0, -1, A]],
        [[-1, 0, A], [0, 1, 0]],
        [[-1, 0, A], [0, -1, A]],
        [[0, 1, 0], [1, 0, 0]],
        [[0, 1, 0], [-1, 0, A]],
        [[0, -1, A], [1, 0, 0]],
        [[0, -1, A], [-1, 0, A]],
    ]

    def expr(row):
        k = row[2]
        for coef, name in ((row[0], 'y'), (row[1], 'x')):
            if coef == 0:
                continue
            if coef == 1:
                if k > 0:
                    return name + ' + ' + str(k)
                if k < 0:
                    return name + ' - ' + str(-k)
                return name
            if k > 0:
                return str(k) + ' - ' + name
            if k < 0:
                return '-' + name + ' - ' + str(-k)
            return '-' + name
        return str(k)

    # Conjugate each symmetry into visible coordinates and emit it as a literal formula.
    items = []
    for P in natives:
        M = mul(mul(F, P + [[0, 0, 1]]), Finv)
        items.append('(' + expr(M[0]) + ', ' + expr(M[1]) + ')')

    mask = int(palette[0])
    lines = [
        'import numpy as np',
        '',
        '# Erased-patch colour in this episode.',
        'MASK = ' + str(mask),
        '',
        'def partners(y, x):',
        '    # Images of visible cell (y, x) under the mosaic symmetry group, in visible coordinates.',
        '    return [' + ', '.join(items) + ']',
        '',
        'def solve(demonstrations, grid):',
        '    g = np.array(grid, dtype=int)',
        '    H, W = g.shape',
        '    for _ in range(64):',
        '        holes = list(zip(*np.where(g == MASK)))',
        '        if not holes:',
        '            break',
        '        new = g.copy()',
        '        changed = False',
        '        for y, x in holes:',
        '            y = int(y)',
        '            x = int(x)',
        '            for py, px in partners(y, x):',
        '                if 0 <= py < H and 0 <= px < W and g[py, px] != MASK:',
        '                    new[y, x] = g[py, px]',
        '                    changed = True',
        '                    break',
        '        g = new',
        '        if not changed:',
        '            break',
        '    return g.tolist()',
    ]
    return '\n'.join(lines) + '\n'
