def build_program(d4, palette):
    d4 = int(d4) % 8
    # Track where the original 'down' (growth) and 'right' (along the source line)
    # unit vectors end up in visible coordinates (row delta, col delta).
    dr = (1, 0)
    dc = (0, 1)
    if d4 >= 4:
        dc = (0, -1)  # reverse each row first
    for _ in range(d4 % 4):
        # clockwise rotation maps a delta (a, b) to (b, -a)
        dr = (dr[1], -dr[0])
        dc = (dc[1], -dc[0])
    if dr[0] != 0:
        layers_expr = 'H'
        length_expr = 'W'
        grow = dr[0]
        along = dc[1]
        acc = 'g[{L}][{P}]'
    else:
        layers_expr = 'W'
        length_expr = 'H'
        grow = dr[1]
        along = dc[0]
        acc = 'g[{P}][{L}]'
    left = -along
    bg = int(palette[7])
    c2 = int(palette[2])
    c5 = int(palette[5])
    left_cell = acc.format(L='prev', P='p + LEFT')
    right_cell = acc.format(L='prev', P='p - LEFT')
    cur_cell = acc.format(L='cur', P='p')
    lines = [
        'BG = %d' % bg,
        'C2 = %d' % c2,
        'C5 = %d' % c5,
        'GROW = %d' % grow,
        'LEFT = %d' % left,
        '',
        'def solve(demonstrations, grid):',
        '    g = [[int(v) for v in row] for row in grid]',
        '    H = len(g)',
        '    W = len(g[0]) if H else 0',
        '    if H == 0 or W == 0:',
        '        return g',
        '    n_layers = %s' % layers_expr,
        '    length = %s' % length_expr,
        '    first = 0 if GROW > 0 else n_layers - 1',
        '    for i in range(1, n_layers):',
        '        cur = first + GROW * i',
        '        prev = cur - GROW',
        '        for p in range(1, length - 1):',
        '            a = %s' % left_cell,
        '            b = %s' % right_cell,
        '            if a != BG and b != BG:',
        '                %s = C5 if a == C2 else C2' % cur_cell,
        '    return g',
        '',
    ]
    return '\n'.join(lines)
