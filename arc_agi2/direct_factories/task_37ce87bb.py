def build_program(d4, palette):
    # Canonical frame: bars grow upward from the bottom edge (vector (-1,0)).
    # Bars are read left to right (vector (0,1)).
    # Map both vectors into visible coordinates with the episode's D4 transform.
    dr, dc = -1, 0
    sr, sc = 0, 1
    if d4 >= 4:
        # Reversing each row negates the column component.
        dc = -dc
        sc = -sc
    for _ in range(d4 % 4):
        # A clockwise rotation maps (dr, dc) to (dc, -dr).
        dr, dc = dc, -dr
        sr, sc = sc, -sr
    vertical = dr != 0
    if vertical:
        base_high = (dr == -1)
        step = sc
    else:
        base_high = (dc == -1)
        step = sr
    header = (
        'BG = ' + repr(int(palette[7])) + '\n'
        'POS = ' + repr(int(palette[8])) + '\n'
        'NEG = ' + repr(int(palette[2])) + '\n'
        'NEW = ' + repr(int(palette[5])) + '\n'
        'BASE_HIGH = ' + repr(bool(base_high)) + '\n'
        'STEP = ' + repr(int(step)) + '\n\n'
    )
    if vertical:
        body = (
            'def solve(demonstrations, grid):\n'
            '    g = [[int(v) for v in row] for row in grid]\n'
            '    H = len(g)\n'
            '    W = len(g[0])\n'
            '    out = [row[:] for row in g]\n'
            '    total = 0\n'
            '    lines = []\n'
            '    for x in range(W):\n'
            '        n = 0\n'
            '        for y in range(H):\n'
            '            v = g[y][x]\n'
            '            if v == POS:\n'
            '                total += 1\n'
            '                n += 1\n'
            '            elif v == NEG:\n'
            '                total -= 1\n'
            '                n += 1\n'
            '            elif v != BG:\n'
            '                n += 1\n'
            '        if n:\n'
            '            lines.append(x)\n'
            '    if not lines or total <= 0:\n'
            '        return out\n'
            '    nx = lines[-1] + 2 if STEP > 0 else lines[0] - 2\n'
            '    if 0 <= nx < W:\n'
            '        for k in range(min(total, H)):\n'
            '            y = H - 1 - k if BASE_HIGH else k\n'
            '            out[y][nx] = NEW\n'
            '    return out\n'
        )
    else:
        body = (
            'def solve(demonstrations, grid):\n'
            '    g = [[int(v) for v in row] for row in grid]\n'
            '    H = len(g)\n'
            '    W = len(g[0])\n'
            '    out = [row[:] for row in g]\n'
            '    total = 0\n'
            '    lines = []\n'
            '    for y in range(H):\n'
            '        n = 0\n'
            '        for x in range(W):\n'
            '            v = g[y][x]\n'
            '            if v == POS:\n'
            '                total += 1\n'
            '                n += 1\n'
            '            elif v == NEG:\n'
            '                total -= 1\n'
            '                n += 1\n'
            '            elif v != BG:\n'
            '                n += 1\n'
            '        if n:\n'
            '            lines.append(y)\n'
            '    if not lines or total <= 0:\n'
            '        return out\n'
            '    ny = lines[-1] + 2 if STEP > 0 else lines[0] - 2\n'
            '    if 0 <= ny < H:\n'
            '        for k in range(min(total, W)):\n'
            '            x = W - 1 - k if BASE_HIGH else k\n'
            '            out[ny][x] = NEW\n'
            '    return out\n'
        )
    return header + body
