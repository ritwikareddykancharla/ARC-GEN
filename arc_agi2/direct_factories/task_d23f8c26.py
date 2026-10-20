def build_program(d4, palette):
    bg = int(palette[0])
    k = int(d4) % 4
    if k % 2 == 0:
        body = (
            "    c = w // 2\n"
            "    for r in range(h):\n"
            "        out[r][c] = g[r][c]\n"
        )
        axis_doc = "centre column (x = width // 2)"
    else:
        body = (
            "    r = h // 2\n"
            "    for c in range(w):\n"
            "        out[r][c] = g[r][c]\n"
        )
        axis_doc = "centre row (y = height // 2)"
    prog = (
        "BG = %d\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    # Keep only the %s; every other cell becomes the background colour.\n"
        "    g = [list(map(int, row)) for row in grid]\n"
        "    h = len(g)\n"
        "    w = len(g[0]) if h else 0\n"
        "    out = [[BG] * w for _ in range(h)]\n"
        "%s"
        "    return out\n"
    ) % (bg, axis_doc, body)
    return prog
