def build_program(d4, palette):
    k = d4 % 4
    bg = int(palette[0])
    pat = int(palette[8])
    ptr = int(palette[4])
    # Canonically the 8-pattern sits above the 4-pointer (direction 'up').
    # A horizontal flip leaves 'up' unchanged. Each clockwise rotation maps up->right->down->left.
    # k=0: pattern above (stack along rows, mirror along columns, near pointer row = min row)
    # k=1: pattern right (stack along cols, mirror along rows, near pointer col = max col)
    # k=2: pattern below (stack along rows, mirror along columns, near pointer row = max row)
    # k=3: pattern left (stack along cols, mirror along rows, near pointer col = min col)
    header = (
        "import numpy as np\n"
        "BG = " + str(bg) + "\n"
        "PAT = " + str(pat) + "\n"
        "PTR = " + str(ptr) + "\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    out = g.copy()\n"
        "    H, W = g.shape\n"
        "    pys, pxs = np.where(g == PTR)\n"
        "    ays, axs = np.where(g == PAT)\n"
        "    if len(pys) == 0 or len(ays) == 0:\n"
        "        return out.tolist()\n"
    )
    if k in (0, 2):
        near = "pys.min()" if k == 0 else "pys.max()"
        body = (
            "    # Pattern and pointer are stacked vertically, so the reflection runs horizontally.\n"
            "    near = " + near + "\n"
            "    lone = pxs[pys == near]\n"
            "    lo, hi = int(pxs.min()), int(pxs.max())\n"
            "    centre = (lo + hi) / 2.0\n"
            "    to_high = float(lone.mean()) > centre\n"
            "    for r, c in zip(ays.tolist(), axs.tolist()):\n"
            "        nc = (2 * hi + 1 - c) if to_high else (2 * lo - 1 - c)\n"
            "        if 0 <= nc < W and out[r, nc] == BG:\n"
            "            out[r, nc] = PAT\n"
            "    return out.tolist()\n"
        )
    else:
        near = "pxs.max()" if k == 1 else "pxs.min()"
        body = (
            "    # Pattern and pointer are stacked horizontally, so the reflection runs vertically.\n"
            "    near = " + near + "\n"
            "    lone = pys[pxs == near]\n"
            "    lo, hi = int(pys.min()), int(pys.max())\n"
            "    centre = (lo + hi) / 2.0\n"
            "    to_high = float(lone.mean()) > centre\n"
            "    for r, c in zip(ays.tolist(), axs.tolist()):\n"
            "        nr = (2 * hi + 1 - r) if to_high else (2 * lo - 1 - r)\n"
            "        if 0 <= nr < H and out[nr, c] == BG:\n"
            "            out[nr, c] = PAT\n"
            "    return out.tolist()\n"
        )
    return header + body
