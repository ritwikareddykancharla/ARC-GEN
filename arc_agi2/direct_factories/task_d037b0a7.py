def build_program(d4, palette):
    # Original mechanism: each non-background pixel paints its colour toward the
    # bottom edge (+row direction) of its column. The colour switches when a later
    # non-background pixel is met along the scan.
    # D4: an optional horizontal mirror (d4>=4) leaves vertical motion unchanged.
    # Each clockwise rotation maps the direction (dr,dc) to (dc,-dr).
    # Result: k=0 down, k=1 left, k=2 up, k=3 right.
    k = int(d4) % 4
    bg = int(palette[0])
    if k == 0:
        outer = "for c in range(w):"
        inner = "for r in range(h):"
        note = "# drip downward: scan each column top to bottom"
    elif k == 1:
        outer = "for r in range(h):"
        inner = "for c in range(w - 1, -1, -1):"
        note = "# drip leftward: scan each row right to left"
    elif k == 2:
        outer = "for c in range(w):"
        inner = "for r in range(h - 1, -1, -1):"
        note = "# drip upward: scan each column bottom to top"
    else:
        outer = "for r in range(h):"
        inner = "for c in range(w):"
        note = "# drip rightward: scan each row left to right"
    lines = [
        "BG = %d" % bg,
        "",
        "def solve(demonstrations, grid):",
        "    g = [[int(v) for v in row] for row in grid]",
        "    h = len(g)",
        "    w = len(g[0]) if h else 0",
        "    " + note,
        "    " + outer,
        "        cur = None",
        "        " + inner,
        "            v = g[r][c]",
        "            if v != BG:",
        "                cur = v",
        "            elif cur is not None:",
        "                g[r][c] = cur",
        "    return g",
        "",
    ]
    return "\n".join(lines)
