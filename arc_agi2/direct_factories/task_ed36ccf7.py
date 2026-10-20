def build_program(d4, palette):
    # Original visible rule: rotate the whole grid 90 degrees counter-clockwise.
    # Conjugating by a pure rotation leaves a rotation unchanged.
    # Conjugating by a reflection reverses its sense, giving a clockwise rotation.
    # Colours are copied unchanged, so the palette has no effect.
    clockwise = int(d4) >= 4
    if clockwise:
        body = (
            "            out[i][j] = g[H - 1 - j][i]\n"
        )
        doc = "Rotate the grid 90 degrees clockwise: input row r becomes output column H-1-r."
    else:
        body = (
            "            out[i][j] = g[j][W - 1 - i]\n"
        )
        doc = "Rotate the grid 90 degrees counter-clockwise: input column c becomes output row W-1-c."
    prog = (
        "def solve(demonstrations, grid):\n"
        "    # " + doc + "\n"
        "    g = [list(row) for row in grid]\n"
        "    H = len(g)\n"
        "    W = len(g[0]) if H else 0\n"
        "    out = [[0] * H for _ in range(W)]\n"
        "    for i in range(W):\n"
        "        for j in range(H):\n"
        + body +
        "    return out\n"
    )
    return prog
