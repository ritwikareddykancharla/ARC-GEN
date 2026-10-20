def build_program(d4, palette):
    k = int(d4) % 8
    r = k % 4
    flipped = k >= 4
    # Original rule: reflect across the main diagonal (transpose).
    # Conjugating by a 90-degree rotation, or by a horizontal flip, swaps the
    # main diagonal with the anti-diagonal. A 180-degree rotation keeps it.
    anti = (r % 2 == 1) != flipped
    if anti:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = [list(row) for row in grid]\n"
            "    h = len(g)\n"
            "    w = len(g[0]) if h else 0\n"
            "    # Reflect across the anti-diagonal: out[i][j] = g[h-1-j][w-1-i]\n"
            "    out = []\n"
            "    for i in range(w):\n"
            "        src_col = w - 1 - i\n"
            "        row = [g[h - 1 - j][src_col] for j in range(h)]\n"
            "        out.append(row)\n"
            "    return out\n"
        )
    else:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = [list(row) for row in grid]\n"
            "    h = len(g)\n"
            "    w = len(g[0]) if h else 0\n"
            "    # Reflect across the main diagonal: out[i][j] = g[j][i]\n"
            "    out = []\n"
            "    for i in range(w):\n"
            "        row = [g[j][i] for j in range(h)]\n"
            "        out.append(row)\n"
            "    return out\n"
        )
    return body
