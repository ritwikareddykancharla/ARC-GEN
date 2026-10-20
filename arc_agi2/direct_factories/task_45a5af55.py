def build_program(d4, palette):
    k = d4 % 4
    # Original: solid rows, ring colour sequence read top->bottom (last row is an unused duplicate).
    # Horizontal flip (d4>=4) keeps solid rows in place, so only rotation matters.
    # k=0: rows, top->bottom; k=1: columns, right->left; k=2: rows, bottom->top; k=3: columns, left->right.
    if k == 0:
        read = "    seq = [int(g[r, 0]) for r in range(g.shape[0])]\n"
    elif k == 1:
        read = "    seq = [int(g[0, c]) for c in range(g.shape[1] - 1, -1, -1)]\n"
    elif k == 2:
        read = "    seq = [int(g[r, 0]) for r in range(g.shape[0] - 1, -1, -1)]\n"
    else:
        read = "    seq = [int(g[0, c]) for c in range(g.shape[1])]\n"
    prog = (
        "import numpy as np\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.asarray(grid, dtype=int)\n"
        + read +
        "    L = len(seq)\n"
        "    N = 2 * (L - 1)\n"
        "    if N < 1:\n"
        "        return [[seq[0]]]\n"
        "    yy, xx = np.indices((N, N))\n"
        "    depth = np.minimum(np.minimum(yy, xx), np.minimum(N - 1 - yy, N - 1 - xx))\n"
        "    out = np.full((N, N), seq[0], dtype=int)\n"
        "    maxd = N // 2 - 1\n"
        "    d = 1\n"
        "    while d <= maxd:\n"
        "        e = d\n"
        "        while e + 1 <= maxd and seq[e + 1] == seq[d]:\n"
        "            e += 1\n"
        "        out[(depth >= d) & (depth <= e)] = seq[d]\n"
        "        d = e + 1\n"
        "    return out.tolist()\n"
    )
    return prog
