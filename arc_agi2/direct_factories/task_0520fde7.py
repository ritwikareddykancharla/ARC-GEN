def build_program(d4, palette):
    bg = int(palette[0])
    div = int(palette[5])
    on = int(palette[1])
    mark = int(palette[2])
    # Original layout: 3x7 grid with a vertical gray divider column.
    # Odd d4 (90/270 degree rotations, with or without the initial row flip)
    # turns the divider column into a divider row.
    horizontal_divider = (d4 % 2 == 1)
    head = (
        "import numpy as np\n"
        "BG = %d\n"
        "DIV = %d\n"
        "ON = %d\n"
        "MARK = %d\n" % (bg, div, on, mark)
    )
    col_code = (
        "def solve(demonstrations, grid):\n"
        "    g = np.asarray(grid, dtype=int)\n"
        "    h, w = g.shape\n"
        "    cand = [x for x in range(w) if bool((g[:, x] == DIV).all())]\n"
        "    if cand:\n"
        "        mid = (w - 1) / 2.0\n"
        "        dx = min(cand, key=lambda x: (abs(x - mid), x))\n"
        "    else:\n"
        "        dx = w // 2\n"
        "    a = g[:, :dx]\n"
        "    b = g[:, dx + 1:]\n"
        "    pw = min(a.shape[1], b.shape[1])\n"
        "    if pw <= 0:\n"
        "        return [[BG]]\n"
        "    a = a[:, :pw]\n"
        "    b = b[:, b.shape[1] - pw:]\n"
        "    out = np.full((h, pw), BG, dtype=int)\n"
        "    out[(a == ON) & (b == ON)] = MARK\n"
        "    return out.tolist()\n"
    )
    row_code = (
        "def solve(demonstrations, grid):\n"
        "    g = np.asarray(grid, dtype=int)\n"
        "    h, w = g.shape\n"
        "    cand = [y for y in range(h) if bool((g[y, :] == DIV).all())]\n"
        "    if cand:\n"
        "        mid = (h - 1) / 2.0\n"
        "        dy = min(cand, key=lambda y: (abs(y - mid), y))\n"
        "    else:\n"
        "        dy = h // 2\n"
        "    a = g[:dy, :]\n"
        "    b = g[dy + 1:, :]\n"
        "    ph = min(a.shape[0], b.shape[0])\n"
        "    if ph <= 0:\n"
        "        return [[BG]]\n"
        "    a = a[:ph, :]\n"
        "    b = b[b.shape[0] - ph:, :]\n"
        "    out = np.full((ph, w), BG, dtype=int)\n"
        "    out[(a == ON) & (b == ON)] = MARK\n"
        "    return out.tolist()\n"
    )
    return head + (row_code if horizontal_divider else col_code)
