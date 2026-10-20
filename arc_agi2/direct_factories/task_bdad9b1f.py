def build_program(d4, palette):
    k = int(d4) % 8
    swap = (k % 4) % 2 == 1
    c_line_a = int(palette[8])
    c_line_b = int(palette[2])
    c_cross = int(palette[4])
    if not swap:
        body = (
            "    a_cols = sorted(set(np.where(g == C_A)[1].tolist()))\n"
            "    b_rows = sorted(set(np.where(g == C_B)[0].tolist()))\n"
            "    for x in a_cols:\n"
            "        out[:, x] = C_A\n"
            "    for y in b_rows:\n"
            "        out[y, :] = C_B\n"
            "    for y in b_rows:\n"
            "        for x in a_cols:\n"
            "            out[y, x] = C_X\n"
        )
    else:
        body = (
            "    a_rows = sorted(set(np.where(g == C_A)[0].tolist()))\n"
            "    b_cols = sorted(set(np.where(g == C_B)[1].tolist()))\n"
            "    for y in a_rows:\n"
            "        out[y, :] = C_A\n"
            "    for x in b_cols:\n"
            "        out[:, x] = C_B\n"
            "    for y in a_rows:\n"
            "        for x in b_cols:\n"
            "            out[y, x] = C_X\n"
        )
    prog = (
        "import numpy as np\n"
        "\n"
        "C_A = " + str(c_line_a) + "\n"
        "C_B = " + str(c_line_b) + "\n"
        "C_X = " + str(c_cross) + "\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    out = g.copy()\n"
        + body +
        "    return out.tolist()\n"
    )
    return prog
