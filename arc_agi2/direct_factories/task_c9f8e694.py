def build_program(d4, palette):
    k = int(d4) % 4
    flip = int(d4) >= 4
    if not flip:
        side = ['left', 'top', 'right', 'bottom'][k]
    else:
        side = ['right', 'bottom', 'left', 'top'][k]
    grey = int(palette[5])
    head = (
        'import numpy as np\n'
        '\n'
        'GREY = ' + str(grey) + '\n'
        '\n'
        'def solve(demonstrations, grid):\n'
        '    g = np.array(grid, dtype=int).copy()\n'
        '    h, w = g.shape\n'
    )
    if side == 'left':
        body = (
            '    for y in range(h):\n'
            '        key = g[y, 0]\n'
            '        seg = g[y, 1:]\n'
            '        seg[seg == GREY] = key\n'
        )
    elif side == 'right':
        body = (
            '    for y in range(h):\n'
            '        key = g[y, w - 1]\n'
            '        seg = g[y, :w - 1]\n'
            '        seg[seg == GREY] = key\n'
        )
    elif side == 'top':
        body = (
            '    for x in range(w):\n'
            '        key = g[0, x]\n'
            '        seg = g[1:, x]\n'
            '        seg[seg == GREY] = key\n'
        )
    else:
        body = (
            '    for x in range(w):\n'
            '        key = g[h - 1, x]\n'
            '        seg = g[:h - 1, x]\n'
            '        seg[seg == GREY] = key\n'
        )
    tail = '    return g.tolist()\n'
    return head + body + tail
