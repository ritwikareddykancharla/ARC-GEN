def build_program(d4, palette):
    bg = int(palette[0])
    fill = int(palette[3])
    div = int(palette[4])
    vertical_divider = (int(d4) % 2) == 1
    header = (
        "import numpy as np\n"
        "BG = %d\n"
        "FILL = %d\n"
        "DIV = %d\n" % (bg, fill, div)
    )
    if not vertical_divider:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    H = g.shape[0]\n"
            "    cands = [y for y in range(1, H - 1) if (g[y, :] == DIV).all()]\n"
            "    if cands:\n"
            "        r = min(cands, key=lambda y: abs(y - (H - 1) / 2.0))\n"
            "        a = g[:r, :]\n"
            "        b = g[r + 1:, :]\n"
            "        h = min(a.shape[0], b.shape[0])\n"
            "        a = a[:h, :]\n"
            "        b = b[b.shape[0] - h:, :]\n"
            "    else:\n"
            "        h = H // 2\n"
            "        a = g[:h, :]\n"
            "        b = g[H - h:, :]\n"
            "    out = np.full(a.shape, BG, dtype=int)\n"
            "    out[(a == BG) & (b == BG)] = FILL\n"
            "    return out.tolist()\n"
        )
    else:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    W = g.shape[1]\n"
            "    cands = [x for x in range(1, W - 1) if (g[:, x] == DIV).all()]\n"
            "    if cands:\n"
            "        c = min(cands, key=lambda x: abs(x - (W - 1) / 2.0))\n"
            "        a = g[:, :c]\n"
            "        b = g[:, c + 1:]\n"
            "        w = min(a.shape[1], b.shape[1])\n"
            "        a = a[:, :w]\n"
            "        b = b[:, b.shape[1] - w:]\n"
            "    else:\n"
            "        w = W // 2\n"
            "        a = g[:, :w]\n"
            "        b = g[:, W - w:]\n"
            "    out = np.full(a.shape, BG, dtype=int)\n"
            "    out[(a == BG) & (b == BG)] = FILL\n"
            "    return out.tolist()\n"
        )
    return header + body
