def build_program(d4, palette):
    bg = int(palette[0])
    two = int(palette[2])
    src = '''import numpy as np

BG = %d
TWO = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    counts = {}
    for v in g.ravel().tolist():
        if v != BG and v != TWO:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return g.tolist()
    best = max(counts.values())
    rc = min(c for c, n in counts.items() if n == best)
    ys, xs = np.nonzero(g == rc)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    oh, ow = out.shape
    centres = {}
    for y in range(H):
        for x in range(W):
            if y0 <= y <= y1 and x0 <= x <= x1:
                continue
            c = int(g[y, x])
            if c != BG and c != TWO and c != rc:
                centres[c] = (y, x)
    marks = []
    for my in range(oh):
        for mx in range(ow):
            c = int(out[my, mx])
            if c == rc or c == TWO or c == BG or c not in centres:
                continue
            marks.append((my, mx, c))
    for my, mx, c in marks:
        cy, cx = centres[c]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                sy, sx = cy + dy, cx + dx
                ty, tx = my + dy, mx + dx
                if not (0 <= sy < H and 0 <= sx < W):
                    continue
                if not (0 <= ty < oh and 0 <= tx < ow):
                    continue
                if g[sy, sx] == TWO:
                    out[ty, tx] = TWO
    return out.tolist()
''' % (bg, two)
    return src
