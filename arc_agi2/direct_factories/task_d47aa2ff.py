def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[i]) for i in range(10)]
    bg = pal[0]
    div = pal[5]
    vac = pal[2]
    arr = pal[1]
    # Original layout: source panel on the LEFT of a vertical divider; output = source panel.
    # After D4 (flip-then-rotate), the source panel lands on:
    # 0:left 1:top 2:right 3:bottom 4:right 5:bottom 6:left 7:top
    vertical = (d4 % 2 == 0)
    source_first = d4 in (0, 1, 6, 7)
    header = (
        "import numpy as np\n\n"
        "BG = __BG__\n"
        "DIV = __DIV__\n"
        "VACATED = __VAC__\n"
        "ARRIVED = __ARR__\n"
        "SOURCE_FIRST = __SF__\n\n"
    )
    if vertical:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    h, w = g.shape\n"
            "    cands = [x for x in range(w) if (g[:, x] == DIV).all()]\n"
            "    if cands:\n"
            "        d = min(cands, key=lambda x: abs(2 * x - (w - 1)))\n"
            "    else:\n"
            "        d = w // 2\n"
            "    first = g[:, :d]\n"
            "    second = g[:, d + 1:]\n"
            "    if SOURCE_FIRST:\n"
            "        src, oth = first, second\n"
            "    else:\n"
            "        src, oth = second, first\n"
            "    out = src.copy()\n"
            "    n = min(src.shape[1], oth.shape[1])\n"
            "    s = src[:, :n]\n"
            "    t = oth[:, :n]\n"
            "    vac = (s != BG) & (t == BG)\n"
            "    arr = (s == BG) & (t != BG)\n"
            "    sub = out[:, :n]\n"
            "    sub[vac] = VACATED\n"
            "    sub[arr] = ARRIVED\n"
            "    return out.tolist()\n"
        )
    else:
        body = (
            "def solve(demonstrations, grid):\n"
            "    g = np.array(grid, dtype=int)\n"
            "    h, w = g.shape\n"
            "    cands = [y for y in range(h) if (g[y, :] == DIV).all()]\n"
            "    if cands:\n"
            "        d = min(cands, key=lambda y: abs(2 * y - (h - 1)))\n"
            "    else:\n"
            "        d = h // 2\n"
            "    first = g[:d, :]\n"
            "    second = g[d + 1:, :]\n"
            "    if SOURCE_FIRST:\n"
            "        src, oth = first, second\n"
            "    else:\n"
            "        src, oth = second, first\n"
            "    out = src.copy()\n"
            "    n = min(src.shape[0], oth.shape[0])\n"
            "    s = src[:n, :]\n"
            "    t = oth[:n, :]\n"
            "    vac = (s != BG) & (t == BG)\n"
            "    arr = (s == BG) & (t != BG)\n"
            "    sub = out[:n, :]\n"
            "    sub[vac] = VACATED\n"
            "    sub[arr] = ARRIVED\n"
            "    return out.tolist()\n"
        )
    code = header + body
    code = code.replace("__BG__", str(bg))
    code = code.replace("__DIV__", str(div))
    code = code.replace("__VAC__", str(vac))
    code = code.replace("__ARR__", str(arr))
    code = code.replace("__SF__", "True" if source_first else "False")
    return code
