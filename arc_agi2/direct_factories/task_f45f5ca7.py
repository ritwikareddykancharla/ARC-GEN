def build_program(d4, palette):
    # The original mechanism: cells sit on the west edge (column 0) and slide east
    # (+column) to a distance that depends only on their colour:
    # 8 -> 1, 2 -> 2, 4 -> 3, 3 -> 4. Unknown colours stay on the source edge.
    # Track where the original 'east' motion vector points in visible coordinates.
    # A row reversal turns east into west. Each clockwise rotation maps
    # E->S, S->W, W->N, N->E.
    order = ['E', 'S', 'W', 'N']
    idx = 0 if d4 < 4 else 2
    idx = (idx + (d4 % 4)) % 4
    direction = order[idx]
    bg = int(palette[0])
    offsets = {
        int(palette[8]): 1,
        int(palette[2]): 2,
        int(palette[4]): 3,
        int(palette[3]): 4,
    }
    if direction == 'E':
        place = '        ny, nx = y, min(k, W - 1)\n'
    elif direction == 'W':
        place = '        ny, nx = y, max(W - 1 - k, 0)\n'
    elif direction == 'S':
        place = '        ny, nx = min(k, H - 1), x\n'
    else:
        place = '        ny, nx = max(H - 1 - k, 0), x\n'
    src = (
        '# Each coloured cell keeps its position across the motion axis.\n'
        '# It is re-placed at a colour-specific distance from the source edge.\n'
        '# Motion direction in visible coordinates: ' + direction + '\n'
        'BG = ' + repr(bg) + '\n'
        'OFFSETS = ' + repr(offsets) + '\n'
        '\n'
        'def solve(demonstrations, grid):\n'
        '    H = len(grid)\n'
        '    W = len(grid[0])\n'
        '    out = [[BG] * W for _ in range(H)]\n'
        '    cells = []\n'
        '    for y in range(H):\n'
        '        for x in range(W):\n'
        '            v = int(grid[y][x])\n'
        '            if v != BG:\n'
        '                cells.append((y, x, v))\n'
        '    cells.sort(key=lambda t: OFFSETS.get(t[2], 0))\n'
        '    for (y, x, v) in cells:\n'
        '        k = OFFSETS.get(v, 0)\n'
        + place +
        '        out[ny][nx] = v\n'
        '    return out\n'
    )
    return src
