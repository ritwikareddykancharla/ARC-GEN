def build_program(d4, palette):
    # The rule is D4-invariant: 4-connectivity, border contact and 4-adjacency
    # are preserved by every rotation and reflection. So the emitted program runs
    # the hole test directly in visible coordinates, using palette constants for
    # the colour roles.
    bg = int(palette[9])
    fg = int(palette[1])
    mark = int(palette[8])
    header = "import numpy as np\nfrom collections import deque\n\nBG = %d\nFG = %d\nMARK = %d\n" % (bg, fg, mark)
    body = """

def _flood(mask, sy, sx, seen):
    H, W = mask.shape
    q = deque([(sy, sx)])
    seen[sy, sx] = True
    cells = []
    while q:
        y, x = q.popleft()
        cells.append((y, x))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return cells


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    bgmask = g == BG
    hole = np.zeros((H, W), dtype=bool)
    seen = np.zeros((H, W), dtype=bool)
    for y in range(H):
        for x in range(W):
            if bgmask[y, x] and not seen[y, x]:
                comp = _flood(bgmask, y, x, seen)
                if not any(cy == 0 or cx == 0 or cy == H - 1 or cx == W - 1 for cy, cx in comp):
                    for cy, cx in comp:
                        hole[cy, cx] = True
    fgmask = g == FG
    seen = np.zeros((H, W), dtype=bool)
    for y in range(H):
        for x in range(W):
            if fgmask[y, x] and not seen[y, x]:
                comp = _flood(fgmask, y, x, seen)
                encl = False
                for cy, cx in comp:
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H and 0 <= nx < W and hole[ny, nx]:
                            encl = True
                            break
                    if encl:
                        break
                if encl:
                    for cy, cx in comp:
                        out[cy, cx] = MARK
    return out.tolist()
"""
    return header + body
