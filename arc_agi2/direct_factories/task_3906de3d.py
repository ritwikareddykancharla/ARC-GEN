def build_program(d4, palette):
    k = int(d4) % 4
    bg = int(palette[0])
    red = int(palette[2])
    # Original mechanism: red cells rise toward the TOP edge, column by column.
    # Under the visible transform, the original 'up' direction (-1,0) becomes:
    # k=0 -> up, k=1 -> right, k=2 -> down, k=3 -> left. The horizontal flip
    # (d4>=4) does not change a vertical direction.
    # Each line is listed starting from the cell on the target edge and moving outward.
    if k == 0:
        lines_src = (
            "def _lines(H, W):\n"
            "    # gravity toward top edge: each column, ordered from row 0 downward\n"
            "    return [[(y, x) for y in range(H)] for x in range(W)]\n"
        )
    elif k == 1:
        lines_src = (
            "def _lines(H, W):\n"
            "    # gravity toward right edge: each row, ordered from column W-1 leftward\n"
            "    return [[(y, x) for x in range(W - 1, -1, -1)] for y in range(H)]\n"
        )
    elif k == 2:
        lines_src = (
            "def _lines(H, W):\n"
            "    # gravity toward bottom edge: each column, ordered from row H-1 upward\n"
            "    return [[(y, x) for y in range(H - 1, -1, -1)] for x in range(W)]\n"
        )
    else:
        lines_src = (
            "def _lines(H, W):\n"
            "    # gravity toward left edge: each row, ordered from column 0 rightward\n"
            "    return [[(y, x) for x in range(W)] for y in range(H)]\n"
        )
    head = (
        "import numpy as np\n"
        "\n"
        "BG = " + str(bg) + "\n"
        "RED = " + str(red) + "\n"
        "\n"
    )
    body = (
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    H, W = g.shape\n"
        "    out = g.copy()\n"
        "    out[out == RED] = BG\n"
        "    for line in _lines(H, W):\n"
        "        idx = [i for i, (y, x) in enumerate(line) if g[y, x] == RED]\n"
        "        if not idx:\n"
        "            continue\n"
        "        n = len(idx)\n"
        "        first = min(idx)\n"
        "        b = -1\n"
        "        for i in range(first - 1, -1, -1):\n"
        "            y, x = line[i]\n"
        "            v = g[y, x]\n"
        "            if v != BG and v != RED:\n"
        "                b = i\n"
        "                break\n"
        "        for j in range(n):\n"
        "            p = b + 1 + j\n"
        "            if p < len(line):\n"
        "                y, x = line[p]\n"
        "                out[y, x] = RED\n"
        "    return out.tolist()\n"
    )
    return head + lines_src + body
