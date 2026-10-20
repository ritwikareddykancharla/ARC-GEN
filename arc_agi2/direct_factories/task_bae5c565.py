def build_program(d4, palette):
    bg = int(palette[5])
    k = int(d4) % 4
    # Original palette edge is the top row. A horizontal flip keeps it on top,
    # so the visible edge depends only on the rotation: 0 top, 1 right, 2 bottom, 3 left.
    # The staircase is symmetric along the palette, so the flip changes nothing in the mechanism.
    head = (
        "import numpy as np\n"
        "\n"
        "BG = " + str(bg) + "\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    H, W = g.shape\n"
        "    out = g.copy()\n"
    )
    if k == 0:
        body = (
            "    pal = g[0, :].copy()\n"
            "    out[0, :] = BG\n"
            "    ys, xs = np.nonzero(g[1:, :] != BG)\n"
            "    if len(xs) == 0:\n"
            "        return out.tolist()\n"
            "    c = int(np.bincount(xs).argmax())\n"
            "    r0 = int(ys[xs == c].min()) + 1\n"
            "    for d in range(1, max(c, W - 1 - c) + 1):\n"
            "        top = r0 + d\n"
            "        if top >= H:\n"
            "            break\n"
            "        for x in (c - d, c + d):\n"
            "            if 0 <= x < W:\n"
            "                out[top:, x] = pal[x]\n"
            "    return out.tolist()\n"
        )
    elif k == 2:
        body = (
            "    pal = g[H - 1, :].copy()\n"
            "    out[H - 1, :] = BG\n"
            "    ys, xs = np.nonzero(g[:H - 1, :] != BG)\n"
            "    if len(xs) == 0:\n"
            "        return out.tolist()\n"
            "    c = int(np.bincount(xs).argmax())\n"
            "    r1 = int(ys[xs == c].max())\n"
            "    for d in range(1, max(c, W - 1 - c) + 1):\n"
            "        bot = r1 - d\n"
            "        if bot < 0:\n"
            "            break\n"
            "        for x in (c - d, c + d):\n"
            "            if 0 <= x < W:\n"
            "                out[:bot + 1, x] = pal[x]\n"
            "    return out.tolist()\n"
        )
    elif k == 3:
        body = (
            "    pal = g[:, 0].copy()\n"
            "    out[:, 0] = BG\n"
            "    ys, xs = np.nonzero(g[:, 1:] != BG)\n"
            "    if len(ys) == 0:\n"
            "        return out.tolist()\n"
            "    r = int(np.bincount(ys).argmax())\n"
            "    c0 = int(xs[ys == r].min()) + 1\n"
            "    for d in range(1, max(r, H - 1 - r) + 1):\n"
            "        left = c0 + d\n"
            "        if left >= W:\n"
            "            break\n"
            "        for y in (r - d, r + d):\n"
            "            if 0 <= y < H:\n"
            "                out[y, left:] = pal[y]\n"
            "    return out.tolist()\n"
        )
    else:
        body = (
            "    pal = g[:, W - 1].copy()\n"
            "    out[:, W - 1] = BG\n"
            "    ys, xs = np.nonzero(g[:, :W - 1] != BG)\n"
            "    if len(ys) == 0:\n"
            "        return out.tolist()\n"
            "    r = int(np.bincount(ys).argmax())\n"
            "    c1 = int(xs[ys == r].max())\n"
            "    for d in range(1, max(r, H - 1 - r) + 1):\n"
            "        right = c1 - d\n"
            "        if right < 0:\n"
            "            break\n"
            "        for y in (r - d, r + d):\n"
            "            if 0 <= y < H:\n"
            "                out[y, :right + 1] = pal[y]\n"
            "    return out.tolist()\n"
        )
    return head + body
