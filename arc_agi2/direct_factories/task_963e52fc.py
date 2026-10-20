def build_program(d4, palette):
    # Original mechanism: the band repeats with a horizontal period; the output is
    # twice as wide, with the input anchored at the left edge and the repetition
    # continued to the right.
    # D4: indices>=4 reverse each row first (extension direction becomes left),
    # then rotate clockwise k times. One clockwise turn maps right->down->left->up->right.
    k = d4 % 4
    seq = ['right', 'down', 'left', 'up']
    start = 2 if d4 >= 4 else 0
    direction = seq[(start + k) % 4]
    # Palette is irrelevant: the colours are copied from the visible input, so
    # there are no colour-role constants.
    if direction in ('right', 'left'):
        off_expr = '0' if direction == 'right' else 'w'
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    h, w = g.shape\n"
            "    # smallest horizontal period over whole columns\n"
            "    p = w\n"
            "    for cand in range(1, w + 1):\n"
            "        if all(np.array_equal(g[:, x], g[:, x - cand]) for x in range(cand, w)):\n"
            "            p = cand\n"
            "            break\n"
            "    off = " + off_expr + "\n"
            "    out = np.zeros((h, 2 * w), dtype=int)\n"
            "    # input occupies columns off..off+w-1; continue the period along the row axis\n"
            "    for x in range(2 * w):\n"
            "        out[:, x] = g[:, (x - off) % p]\n"
            "    return out.tolist()\n"
        )
    else:
        off_expr = '0' if direction == 'down' else 'h'
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    h, w = g.shape\n"
            "    # smallest vertical period over whole rows\n"
            "    p = h\n"
            "    for cand in range(1, h + 1):\n"
            "        if all(np.array_equal(g[y, :], g[y - cand, :]) for y in range(cand, h)):\n"
            "            p = cand\n"
            "            break\n"
            "    off = " + off_expr + "\n"
            "    out = np.zeros((2 * h, w), dtype=int)\n"
            "    # input occupies rows off..off+h-1; continue the period along the column axis\n"
            "    for y in range(2 * h):\n"
            "        out[y, :] = g[(y - off) % p, :]\n"
            "    return out.tolist()\n"
        )
    return "import numpy as np\n\n" + body
