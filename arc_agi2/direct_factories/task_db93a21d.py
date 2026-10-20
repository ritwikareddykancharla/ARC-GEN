def build_program(d4, palette):
    k = int(d4) % 4
    block = int(palette[9])
    frame = int(palette[3])
    beam = int(palette[1])
    # Original beam goes DOWN. Horizontal reflection (d4>=4) leaves the vertical
    # vector unchanged. Each clockwise turn maps (dr, dc) -> (dc, -dr):
    # down -> left -> up -> right.
    if k == 0:
        beam_code = (
            "        s = y1 + b + 1\n"
            "        if s < H:\n"
            "            out[s:, x0:x1 + 1] = BEAM\n")
    elif k == 1:
        beam_code = (
            "        e = x0 - b\n"
            "        if e > 0:\n"
            "            out[y0:y1 + 1, :e] = BEAM\n")
    elif k == 2:
        beam_code = (
            "        e = y0 - b\n"
            "        if e > 0:\n"
            "            out[:e, x0:x1 + 1] = BEAM\n")
    else:
        beam_code = (
            "        s = x1 + b + 1\n"
            "        if s < W:\n"
            "            out[y0:y1 + 1, s:] = BEAM\n")
    src = (
        "import numpy as np\n"
        "from collections import deque\n"
        "\n"
        "BLOCK = " + repr(block) + "\n"
        "FRAME = " + repr(frame) + "\n"
        "BEAM = " + repr(beam) + "\n"
        "\n"
        "def _boxes(mask):\n"
        "    H, W = mask.shape\n"
        "    seen = np.zeros((H, W), dtype=bool)\n"
        "    out = []\n"
        "    for y in range(H):\n"
        "        for x in range(W):\n"
        "            if mask[y, x] and not seen[y, x]:\n"
        "                seen[y, x] = True\n"
        "                q = deque([(y, x)])\n"
        "                y0, x0, y1, x1 = y, x, y, x\n"
        "                while q:\n"
        "                    cy, cx = q.popleft()\n"
        "                    if cy < y0: y0 = cy\n"
        "                    if cy > y1: y1 = cy\n"
        "                    if cx < x0: x0 = cx\n"
        "                    if cx > x1: x1 = cx\n"
        "                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n"
        "                        ny, nx = cy + dy, cx + dx\n"
        "                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:\n"
        "                            seen[ny, nx] = True\n"
        "                            q.append((ny, nx))\n"
        "                out.append((y0, x0, y1, x1))\n"
        "    return out\n"
        "\n"
        "def solve(demonstrations, grid):\n"
        "    g = np.array(grid, dtype=int)\n"
        "    H, W = g.shape\n"
        "    out = g.copy()\n"
        "    mask = g == BLOCK\n"
        "    frames = []\n"
        "    for (y0, x0, y1, x1) in _boxes(mask):\n"
        "        b = max(y1 - y0 + 1, x1 - x0 + 1) // 2\n"
        "        frames.append((max(0, y0 - b), max(0, x0 - b), min(H - 1, y1 + b), min(W - 1, x1 + b)))\n"
        + beam_code +
        "    for fy0, fx0, fy1, fx1 in frames:\n"
        "        out[fy0:fy1 + 1, fx0:fx1 + 1] = FRAME\n"
        "    out[mask] = g[mask]\n"
        "    return out.tolist()\n"
    )
    return src
