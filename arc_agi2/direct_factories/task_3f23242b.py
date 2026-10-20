def build_program(d4, palette):
    k = d4 % 4
    flip = d4 >= 4

    def tv(dy, dx):
        # Map a native offset vector into visible coordinates.
        # Reversing each row negates dx; one clockwise rotation maps (dy, dx) to (dx, -dy).
        if flip:
            dx = -dx
        for _ in range(k):
            dy, dx = dx, -dy
        return dy, dx

    native = []
    for dx in range(-2, 3):
        native.append((-2, dx, 5))
        native.append((2, dx, 8))
    native.append((-1, 0, 5))
    for dy in (-1, 0, 1):
        native.append((dy, -2, 2))
        native.append((dy, 2, 2))
    native.append((0, 0, 3))
    stamps = []
    for dy, dx, c in native:
        vy, vx = tv(dy, dx)
        stamps.append((vy, vx, int(palette[c])))
    ly, lx = tv(2, 0)
    seed = int(palette[3])
    line = int(palette[2])
    if ly != 0:
        line_code = (
            "        yy = y + (%d)\n"
            "        if 0 <= yy < H:\n"
            "            out[yy, :] = LINE\n" % ly
        )
    else:
        line_code = (
            "        xx = x + (%d)\n"
            "        if 0 <= xx < W:\n"
            "            out[:, xx] = LINE\n" % lx
        )
    prog = (
        "import numpy as np\n"
        "SEED = %d\n"
        "LINE = %d\n"
        "STAMPS = %r\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    out = g.copy()\n"
        "    H, W = g.shape\n"
        "    seeds = [(int(y), int(x)) for y, x in zip(*np.where(g == SEED))]\n"
        "    for y, x in seeds:\n"
        "%s"
        "    for y, x in seeds:\n"
        "        for dy, dx, c in STAMPS:\n"
        "            yy, xx = y + dy, x + dx\n"
        "            if 0 <= yy < H and 0 <= xx < W:\n"
        "                out[yy, xx] = c\n"
        "    return out.tolist()\n"
    ) % (seed, line, stamps, line_code)
    return prog
