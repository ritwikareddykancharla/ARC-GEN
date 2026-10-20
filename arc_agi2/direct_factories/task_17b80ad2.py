def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    mk = int(palette[5])
    head = (
        "def solve(demonstrations, grid):\n"
        "    g = [list(map(int, row)) for row in grid]\n"
        "    out = [row[:] for row in g]\n"
        "    h = len(g)\n"
        "    w = len(g[0]) if h else 0\n"
        "    BG = %d\n"
        "    MK = %d\n" % (bg, mk)
    )
    if k == 0:
        body = (
            "    # marker edge: bottom row; flood upward\n"
            "    for x in range(w):\n"
            "        if g[h - 1][x] != MK:\n"
            "            continue\n"
            "        cur = None\n"
            "        for y in range(h - 1, -1, -1):\n"
            "            if g[y][x] != BG:\n"
            "                cur = g[y][x]\n"
            "            elif cur is not None:\n"
            "                out[y][x] = cur\n"
        )
    elif k == 1:
        body = (
            "    # marker edge: left column; flood rightward\n"
            "    for y in range(h):\n"
            "        if g[y][0] != MK:\n"
            "            continue\n"
            "        cur = None\n"
            "        for x in range(0, w):\n"
            "            if g[y][x] != BG:\n"
            "                cur = g[y][x]\n"
            "            elif cur is not None:\n"
            "                out[y][x] = cur\n"
        )
    elif k == 2:
        body = (
            "    # marker edge: top row; flood downward\n"
            "    for x in range(w):\n"
            "        if g[0][x] != MK:\n"
            "            continue\n"
            "        cur = None\n"
            "        for y in range(0, h):\n"
            "            if g[y][x] != BG:\n"
            "                cur = g[y][x]\n"
            "            elif cur is not None:\n"
            "                out[y][x] = cur\n"
        )
    else:
        body = (
            "    # marker edge: right column; flood leftward\n"
            "    for y in range(h):\n"
            "        if g[y][w - 1] != MK:\n"
            "            continue\n"
            "        cur = None\n"
            "        for x in range(w - 1, -1, -1):\n"
            "            if g[y][x] != BG:\n"
            "                cur = g[y][x]\n"
            "            elif cur is not None:\n"
            "                out[y][x] = cur\n"
        )
    tail = "    return out\n"
    return head + body + tail
