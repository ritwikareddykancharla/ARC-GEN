def build_program(d4, palette):
    k = d4 % 4
    along_rows = (k % 2 == 0)
    from_start = k in (0, 3)
    src = int(palette[1])
    dst = int(palette[2])
    head = (
        "import numpy as np\n"
        "SRC = " + str(src) + "\n"
        "DST = " + str(dst) + "\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    h, w = g.shape\n"
        "    rec = g.copy()\n"
        "    rec[g == SRC] = DST\n"
    )
    if along_rows and from_start:
        body = (
            "    # pattern repeats down the rows, anchored at the top, extended downward\n"
            "    n = h\n"
            "    p = n\n"
            "    for cand in range(1, n + 1):\n"
            "        if all(np.array_equal(g[i], g[i + cand]) for i in range(n - cand)):\n"
            "            p = cand\n"
            "            break\n"
            "    N = n * 3 // 2\n"
            "    out = np.zeros((N, w), dtype=int)\n"
            "    for y in range(N):\n"
            "        out[y, :] = rec[y % p, :]\n"
            "    return out.tolist()\n"
        )
    elif along_rows:
        body = (
            "    # pattern repeats up the rows, anchored at the bottom, extended upward\n"
            "    n = h\n"
            "    p = n\n"
            "    for cand in range(1, n + 1):\n"
            "        if all(np.array_equal(g[h - 1 - i], g[h - 1 - i - cand]) for i in range(n - cand)):\n"
            "            p = cand\n"
            "            break\n"
            "    N = n * 3 // 2\n"
            "    out = np.zeros((N, w), dtype=int)\n"
            "    for y in range(N):\n"
            "        out[N - 1 - y, :] = rec[h - 1 - (y % p), :]\n"
            "    return out.tolist()\n"
        )
    elif from_start:
        body = (
            "    # pattern repeats across columns, anchored at the left, extended rightward\n"
            "    n = w\n"
            "    p = n\n"
            "    for cand in range(1, n + 1):\n"
            "        if all(np.array_equal(g[:, i], g[:, i + cand]) for i in range(n - cand)):\n"
            "            p = cand\n"
            "            break\n"
            "    N = n * 3 // 2\n"
            "    out = np.zeros((h, N), dtype=int)\n"
            "    for x in range(N):\n"
            "        out[:, x] = rec[:, x % p]\n"
            "    return out.tolist()\n"
        )
    else:
        body = (
            "    # pattern repeats across columns, anchored at the right, extended leftward\n"
            "    n = w\n"
            "    p = n\n"
            "    for cand in range(1, n + 1):\n"
            "        if all(np.array_equal(g[:, w - 1 - i], g[:, w - 1 - i - cand]) for i in range(n - cand)):\n"
            "            p = cand\n"
            "            break\n"
            "    N = n * 3 // 2\n"
            "    out = np.zeros((h, N), dtype=int)\n"
            "    for x in range(N):\n"
            "        out[:, N - 1 - x] = rec[:, w - 1 - (x % p)]\n"
            "    return out.tolist()\n"
        )
    return head + body
