def build_program(d4, palette):
    k = int(d4)
    D = (1, 0)
    R = (0, 1)
    if k >= 4:
        D = (D[0], -D[1])
        R = (R[0], -R[1])
    for _ in range(k % 4):
        D = (D[1], -D[0])
        R = (R[1], -R[0])
    empty = int(palette[0])
    water = int(palette[1])
    header = ('import numpy as np\n'
              'EMPTY = %d\n'
              'WATER = %d\n'
              'DY, DX = %d, %d\n'
              'RY, RX = %d, %d\n') % (empty, water, D[0], D[1], R[0], R[1])
    body = '''
def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    H, W = g.shape
    cells = [(int(y), int(x)) for y, x in zip(*np.where(g == WATER))]
    n = len(cells)
    if n == 0:
        return g.tolist()
    src = min(cells, key=lambda p: (p[0] * DY + p[1] * DX, p[0] * RY + p[1] * RX))
    for y, x in cells:
        g[y, x] = EMPTY

    def inb(y, x):
        return 0 <= y < H and 0 <= x < W

    def open_below(y, x):
        ny, nx = y + DY, x + DX
        return inb(ny, nx) and g[ny, nx] == EMPTY

    for _ in range(n):
        y, x = src
        if g[y, x] != EMPTY:
            break
        for _ in range(4 * H * W + 10):
            if open_below(y, x):
                y += DY
                x += DX
                continue
            best = None
            for s in (-1, 1):
                cy, cx, dist = y, x, 0
                while True:
                    cy += s * RY
                    cx += s * RX
                    dist += 1
                    if not inb(cy, cx) or g[cy, cx] != EMPTY:
                        break
                    if open_below(cy, cx):
                        if best is None or dist < best[0]:
                            best = (dist, cy, cx)
                        break
            if best is None:
                break
            y, x = best[1], best[2]
        g[y, x] = WATER
    return g.tolist()
'''
    return header + body
