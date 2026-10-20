def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    # Canonical chart: H rows x 5 cols, colour bar in legend column, anchored at bottom.
    # Visible-coordinate rewrite per D4 (flip rows first for d4>=4, then rotate cw d4%4):
    #  even d4 -> bars are vertical (5 columns wide); odd d4 -> bars horizontal (5 rows tall)
    #  slot order reversed for d4 in {2,3,4,5}
    #  bars anchored at far edge (bottom/right) for d4 in {0,3,4,7}, near edge (top/left) otherwise
    vertical = (d4 % 2 == 0)
    reverse = d4 in (2, 3, 4, 5)
    far = d4 in (0, 3, 4, 7)
    legend = {}
    for c, s in ((5, 0), (2, 1), (8, 2), (9, 3), (6, 4)):
        legend[pal[c]] = (4 - s) if reverse else s
    lines = [
        "from collections import deque",
        "BG = %d" % pal[7],
        "SLOTS = %r" % (legend,),
        "VERTICAL = %r" % vertical,
        "FAR = %r" % far,
        "",
        "def _count8(g, colour):",
        "    h = len(g)",
        "    w = len(g[0]) if h else 0",
        "    seen = [[False] * w for _ in range(h)]",
        "    n = 0",
        "    for y in range(h):",
        "        for x in range(w):",
        "            if g[y][x] == colour and not seen[y][x]:",
        "                n += 1",
        "                seen[y][x] = True",
        "                q = deque([(y, x)])",
        "                while q:",
        "                    cy, cx = q.popleft()",
        "                    for dy in (-1, 0, 1):",
        "                        for dx in (-1, 0, 1):",
        "                            ny, nx = cy + dy, cx + dx",
        "                            if 0 <= ny < h and 0 <= nx < w and not seen[ny][nx] and g[ny][nx] == colour:",
        "                                seen[ny][nx] = True",
        "                                q.append((ny, nx))",
        "    return n",
        "",
        "def solve(demonstrations, grid):",
        "    g = [[int(v) for v in row] for row in grid]",
        "    counts = {}",
        "    for c in SLOTS:",
        "        if c == BG:",
        "            continue",
        "        n = _count8(g, c)",
        "        if n > 0:",
        "            counts[c] = n",
        "    H = max(counts.values()) if counts else 1",
        "    if VERTICAL:",
        "        out = [[BG] * 5 for _ in range(H)]",
        "    else:",
        "        out = [[BG] * H for _ in range(5)]",
        "    for c, n in counts.items():",
        "        s = SLOTS[c]",
        "        span = range(H - n, H) if FAR else range(n)",
        "        for t in span:",
        "            if VERTICAL:",
        "                out[t][s] = c",
        "            else:",
        "                out[s][t] = c",
        "    return out",
    ]
    return "\n".join(lines) + "\n"
