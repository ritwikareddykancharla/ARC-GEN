def build_program(d4, palette):
    # Original mechanism: ray goes right (0,1) to the border, then the leg goes down (1,0)
    # along the far border until it meets a coloured cell or the edge.
    adr, adc = 0, 1
    bdr, bdc = 1, 0
    if d4 >= 4:
        # reverse each row: column direction flips
        adc = -adc
        bdc = -bdc
    for _ in range(d4 % 4):
        # clockwise rotation maps direction (dr, dc) -> (dc, -dr)
        adr, adc = adc, -adr
        bdr, bdc = bdc, -bdr
    bg = int(palette[0])
    lines = [
        "import numpy as np",
        "RAY = (%d, %d)" % (adr, adc),
        "LEG = (%d, %d)" % (bdr, bdc),
        "BG = %d" % bg,
        "def solve(demonstrations, grid):",
        "    g = np.array(grid, dtype=int)",
        "    H, W = g.shape",
        "    seeds = [(y, x, int(g[y, x])) for y in range(H) for x in range(W) if g[y, x] != BG]",
        "    ends = []",
        "    for y, x, c in seeds:",
        "        while True:",
        "            g[y, x] = c",
        "            ny, nx = y + RAY[0], x + RAY[1]",
        "            if not (0 <= ny < H and 0 <= nx < W):",
        "                break",
        "            y, x = ny, nx",
        "        ends.append((y, x, c))",
        "    for y, x, c in ends:",
        "        y, x = y + LEG[0], x + LEG[1]",
        "        while 0 <= y < H and 0 <= x < W and g[y, x] == BG:",
        "            g[y, x] = c",
        "            y, x = y + LEG[0], x + LEG[1]",
        "    return g.tolist()",
    ]
    return "\n".join(lines) + "\n"
