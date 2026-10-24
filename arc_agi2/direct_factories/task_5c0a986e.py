# Repair (RE-ARC domain review): every 4-connected component of a ray colour
# emits its own diagonal ray from the bounding-box corner furthest along the
# transformed direction. The native constructor draws one square per colour,
# for which this is identical to the former per-colour bounding box. RE-ARC
# draws several squares per colour and its verifier shoots one ray per
# univalued four-connected object. Rays still paint background cells only.
def build_program(d4, palette):
    def tf(dr, dc):
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc
    d1 = tf(-1, -1)
    d2 = tf(1, 1)
    bg = int(palette[0])
    c1 = int(palette[1])
    c2 = int(palette[2])
    src = '''import numpy as np

BG = %d
RAYS = [(%d, (%d, %d)), (%d, (%d, %d))]

def _components(mask):
    H, W = mask.shape
    seen = np.zeros((H, W), dtype=bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    orig = g.copy()
    for colour, (dr, dc) in RAYS:
        for cells in _components(orig == colour):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            y = (max(ys) if dr > 0 else min(ys)) + dr
            x = (max(xs) if dc > 0 else min(xs)) + dc
            while 0 <= y < H and 0 <= x < W:
                if g[y, x] == BG:
                    g[y, x] = colour
                y += dr
                x += dc
    return g.tolist()
''' % (bg, c1, d1[0], d1[1], c2, d2[0], d2[1])
    return src
