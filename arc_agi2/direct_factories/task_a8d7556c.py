def build_program(d4, palette):
    empty = int(palette[0])
    red = int(palette[2])
    # The generator first paints 'downstripes' (2x2 holes whose LEFT/RIGHT neighbour
    # column pairs are not both empty), then 'sidestripes' (holes whose TOP/BOTTOM
    # neighbour row pairs are not both empty). An odd number of quarter turns swaps
    # the visible axes. A reflection alone does not swap them.
    if d4 % 2 == 0:
        order = "('h', 'v')"
    else:
        order = "('v', 'h')"
    lines = [
        'EMPTY = %d' % empty,
        'RED = %d' % red,
        'ORDER = %s' % order,
        '',
        'def solve(demonstrations, grid):',
        '    out = [list(row) for row in grid]',
        '    H = len(out)',
        '    W = len(out[0]) if H else 0',
        '    def e(r, c):',
        '        return out[r][c] == EMPTY',
        '    for phase in ORDER:',
        '        todo = []',
        '        for r in range(H - 1):',
        '            for c in range(W - 1):',
        '                if not (e(r, c) and e(r, c + 1) and e(r + 1, c) and e(r + 1, c + 1)):',
        '                    continue',
        "                if phase == 'h':",
        '                    if c > 0 and e(r, c - 1) and e(r + 1, c - 1):',
        '                        continue',
        '                    if c < W - 2 and e(r, c + 2) and e(r + 1, c + 2):',
        '                        continue',
        '                else:',
        '                    if r > 0 and e(r - 1, c) and e(r - 1, c + 1):',
        '                        continue',
        '                    if r < H - 2 and e(r + 2, c) and e(r + 2, c + 1):',
        '                        continue',
        '                todo.append((r, c))',
        '        for (r, c) in todo:',
        '            out[r][c] = RED',
        '            out[r][c + 1] = RED',
        '            out[r + 1][c] = RED',
        '            out[r + 1][c + 1] = RED',
        '    return out',
        ''
    ]
    return '\n'.join(lines)
