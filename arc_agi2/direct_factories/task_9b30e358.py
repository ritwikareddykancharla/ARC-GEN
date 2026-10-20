def build_program(d4, palette):
    k = d4 % 4
    # Where the original bottom-edge motif lands after the visible D4 transform.
    # k=0: bottom edge, tile upward; k=1: left edge, tile rightward;
    # k=2: top edge, tile downward;  k=3: right edge, tile leftward.
    # A horizontal flip (d4>=4) does not move the bottom edge, so only k matters.
    header = (
        "from collections import Counter\n"
        "\n"
        "def _bg(g):\n"
        "    c = Counter(v for row in g for v in row)\n"
        "    return c.most_common(1)[0][0]\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = [list(map(int, r)) for r in grid]\n"
        "    H = len(g)\n"
        "    W = len(g[0])\n"
        "    bg = _bg(g)\n"
        "    out = [list(r) for r in g]\n"
    )
    if k == 0:
        body = (
            "    # motif sits on the bottom edge; repeat it upward with period = its height\n"
            "    rows = [y for y in range(H) if any(v != bg for v in g[y])]\n"
            "    if not rows:\n"
            "        return out\n"
            "    y0 = rows[0]\n"
            "    h = H - y0\n"
            "    for y in range(y0):\n"
            "        out[y] = list(g[y0 + (y - y0) % h])\n"
            "    return out\n"
        )
    elif k == 2:
        body = (
            "    # motif sits on the top edge; repeat it downward with period = its height\n"
            "    rows = [y for y in range(H) if any(v != bg for v in g[y])]\n"
            "    if not rows:\n"
            "        return out\n"
            "    h = rows[-1] + 1\n"
            "    for y in range(h, H):\n"
            "        out[y] = list(g[y % h])\n"
            "    return out\n"
        )
    elif k == 1:
        body = (
            "    # motif sits on the left edge; repeat it rightward with period = its width\n"
            "    cols = [x for x in range(W) if any(g[y][x] != bg for y in range(H))]\n"
            "    if not cols:\n"
            "        return out\n"
            "    w = cols[-1] + 1\n"
            "    for x in range(w, W):\n"
            "        sx = x % w\n"
            "        for y in range(H):\n"
            "            out[y][x] = g[y][sx]\n"
            "    return out\n"
        )
    else:
        body = (
            "    # motif sits on the right edge; repeat it leftward with period = its width\n"
            "    cols = [x for x in range(W) if any(g[y][x] != bg for y in range(H))]\n"
            "    if not cols:\n"
            "        return out\n"
            "    x0 = cols[0]\n"
            "    w = W - x0\n"
            "    for x in range(x0):\n"
            "        sx = x0 + (x - x0) % w\n"
            "        for y in range(H):\n"
            "            out[y][x] = g[y][sx]\n"
            "    return out\n"
        )
    return header + body
