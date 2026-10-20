def build_program(d4, palette):
    # Canonical frame: bars grow upward (vector (-1,0)) from the bottom edge,
    # and bar index increases left-to-right (vector (0,1)).
    gr, gc = -1, 0
    orr, oc = 0, 1
    if d4 >= 4:
        # reverse each row: (dr, dc) -> (dr, -dc)
        gc = -gc
        oc = -oc
    for _ in range(d4 % 4):
        # rotate clockwise: (dr, dc) -> (dc, -dr)
        gr, gc = gc, -gr
        orr, oc = oc, -orr
    bg = int(palette[7])
    header = (
        "import numpy as np\n"
        "from collections import Counter\n"
        "BG = " + str(bg) + "\n"
        "GR = " + str(gr) + "\n"
        "GC = " + str(gc) + "\n"
        "OR = " + str(orr) + "\n"
        "OC = " + str(oc) + "\n"
    )
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    vertical = GR != 0          # bars lie along columns when growth is vertical
    growth = GR if vertical else GC
    sign = OC if vertical else OR
    limit = H if vertical else W
    lines = {}
    for r in range(H):
        for c in range(W):
            v = int(g[r, c])
            if v != BG:
                k = c if vertical else r
                p = r if vertical else c
                lines.setdefault(k, []).append((p, v))
    if not lines:
        return g.tolist()
    keys = sorted(lines, key=lambda k: k * sign)
    allp = [p for k in keys for p, _ in lines[k]]
    base = max(allp) if growth < 0 else min(allp)
    colours = []
    heights = []
    for k in keys:
        cells = lines[k]
        colours.append(Counter(v for _, v in cells).most_common(1)[0][0])
        far = min(p for p, _ in cells) if growth < 0 else max(p for p, _ in cells)
        heights.append(abs(base - far) + 1)
    n = len(keys)
    out = g.copy()
    for k in keys:
        for p, _ in lines[k]:
            if vertical:
                out[p, k] = BG
            else:
                out[k, p] = BG
    for i, k in enumerate(keys):
        col = colours[(i - 1) % n]
        h = heights[(i + 1) % n]
        for t in range(h):
            p = base + growth * t
            if 0 <= p < limit:
                if vertical:
                    out[p, k] = col
                else:
                    out[k, p] = col
    return out.tolist()
'''
    return header + body
