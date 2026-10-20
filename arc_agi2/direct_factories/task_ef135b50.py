def build_program(d4, palette):
    red = int(palette[2])
    fill = int(palette[9])
    bg = int(palette[0])
    k = int(d4) % 4
    vertical = (k % 2 == 1)
    header = (
        "RED = %d\n"
        "FILL = %d\n"
        "BG = %d\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = [list(map(int, row)) for row in grid]\n"
        "    h = len(g)\n"
        "    w = len(g[0]) if h else 0\n"
        "    out = [row[:] for row in g]\n"
    ) % (red, fill, bg)
    if not vertical:
        body = (
            "    # channels run along rows; a channel is blocked if any of its cells\n"
            "    # has a red cell directly above or below it\n"
            "    for y in range(h):\n"
            "        reds = [x for x in range(w) if g[y][x] == RED]\n"
            "        for a, b in zip(reds, reds[1:]):\n"
            "            if b - a <= 1:\n"
            "                continue\n"
            "            xs = range(a + 1, b)\n"
            "            if not all(g[y][x] == BG for x in xs):\n"
            "                continue\n"
            "            touches = False\n"
            "            for x in xs:\n"
            "                if y > 0 and g[y - 1][x] == RED:\n"
            "                    touches = True\n"
            "                    break\n"
            "                if y < h - 1 and g[y + 1][x] == RED:\n"
            "                    touches = True\n"
            "                    break\n"
            "            if touches:\n"
            "                continue\n"
            "            for x in xs:\n"
            "                out[y][x] = FILL\n"
            "    return out\n"
        )
    else:
        body = (
            "    # channels run along columns; a channel is blocked if any of its cells\n"
            "    # has a red cell directly left or right of it\n"
            "    for x in range(w):\n"
            "        reds = [y for y in range(h) if g[y][x] == RED]\n"
            "        for a, b in zip(reds, reds[1:]):\n"
            "            if b - a <= 1:\n"
            "                continue\n"
            "            ys = range(a + 1, b)\n"
            "            if not all(g[y][x] == BG for y in ys):\n"
            "                continue\n"
            "            touches = False\n"
            "            for y in ys:\n"
            "                if x > 0 and g[y][x - 1] == RED:\n"
            "                    touches = True\n"
            "                    break\n"
            "                if x < w - 1 and g[y][x + 1] == RED:\n"
            "                    touches = True\n"
            "                    break\n"
            "            if touches:\n"
            "                continue\n"
            "            for y in ys:\n"
            "                out[y][x] = FILL\n"
            "    return out\n"
        )
    return header + body
