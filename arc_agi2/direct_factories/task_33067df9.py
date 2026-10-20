def build_program(d4, palette):
    bg = int(palette[0])
    transposed = (int(d4) % 4) % 2 == 1
    header = (
        "import numpy as np\n"
        "\n"
        "BG = " + str(bg) + "\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    cg = g[1::2, 1::2]\n"
        "    R, C = cg.shape\n"
        "    N = 26\n"
        "    bh = (22 - 2 * (R - 1)) // R\n"
        "    bw = (22 - 2 * (C - 1)) // C\n"
        "    out = np.full((N, N), BG, dtype=int)\n"
        "    def ry(r):\n"
        "        return 2 + r * (bh + 2)\n"
        "    def cx(c):\n"
        "        return 2 + c * (bw + 2)\n"
        "    for r in range(R):\n"
        "        for c in range(C):\n"
        "            col = int(cg[r, c])\n"
        "            if col != BG:\n"
        "                out[ry(r):ry(r) + bh, cx(c):cx(c) + bw] = col\n"
        "    taken = np.zeros((R, C), dtype=bool)\n"
    )
    if not transposed:
        body = (
            "    # primary (always) merging runs along visible rows\n"
            "    for r in range(R):\n"
            "        for c in range(1, C):\n"
            "            if cg[r, c] == cg[r, c - 1]:\n"
            "                taken[r, c] = True\n"
            "                taken[r, c - 1] = True\n"
            "                if int(cg[r, c]) != BG:\n"
            "                    out[ry(r):ry(r) + bh, cx(c) - 2:cx(c)] = int(cg[r, c])\n"
            "    # selective merging along visible columns: only single-cell runs\n"
            "    for c in range(C):\n"
            "        for r in range(1, R):\n"
            "            if cg[r, c] == cg[r - 1, c] and int(cg[r, c]) != BG and not taken[r, c] and not taken[r - 1, c]:\n"
            "                out[ry(r) - 2:ry(r), cx(c):cx(c) + bw] = int(cg[r, c])\n"
        )
    else:
        body = (
            "    # primary (always) merging runs along visible columns\n"
            "    for c in range(C):\n"
            "        for r in range(1, R):\n"
            "            if cg[r, c] == cg[r - 1, c]:\n"
            "                taken[r, c] = True\n"
            "                taken[r - 1, c] = True\n"
            "                if int(cg[r, c]) != BG:\n"
            "                    out[ry(r) - 2:ry(r), cx(c):cx(c) + bw] = int(cg[r, c])\n"
            "    # selective merging along visible rows: only single-cell runs\n"
            "    for r in range(R):\n"
            "        for c in range(1, C):\n"
            "            if cg[r, c] == cg[r, c - 1] and int(cg[r, c]) != BG and not taken[r, c] and not taken[r, c - 1]:\n"
            "                out[ry(r):ry(r) + bh, cx(c) - 2:cx(c)] = int(cg[r, c])\n"
        )
    footer = "    return out.tolist()\n"
    return header + body + footer
