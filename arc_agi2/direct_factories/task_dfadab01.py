def build_program(d4, palette):
    base = {
        2: (4, [[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]]),
        3: (1, [[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]]),
        5: (6, [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]]),
        8: (7, [[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]]),
    }

    def tf(p):
        p = [list(r) for r in p]
        if d4 >= 4:
            p = [r[::-1] for r in p]
        for _ in range(d4 % 4):
            p = [list(r) for r in zip(*p[::-1])]
        return p

    idx = tf([[i * 4 + j for j in range(4)] for i in range(4)])
    anchor = None
    corner = None
    for i in range(4):
        for j in range(4):
            if idx[i][j] == 0:
                anchor = (i, j)
            if idx[i][j] == 15:
                corner = (i, j)
    kdy = 1 if corner[0] == 3 else -1
    kdx = 1 if corner[1] == 3 else -1
    table = {}
    for k, (col, pat) in base.items():
        table[int(palette[k])] = (int(palette[col]), tf(pat))
    bg = int(palette[0])

    src = '''
BG = %r
TABLE = %r
ANCHOR = %r
KDY = %r
KDX = %r


def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0])
    seen = [[False] * W for _ in range(H)]
    ignore = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] == BG or seen[y][x]:
                continue
            col = g[y][x]
            stack = [(y, x)]
            seen[y][x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny][nx] and g[ny][nx] == col:
                            seen[ny][nx] = True
                            stack.append((ny, nx))
            if len(cells) > 1:
                for c in cells:
                    ignore.add(c)
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                ky = (max(ys) if KDY > 0 else min(ys)) + KDY
                kx = (max(xs) if KDX > 0 else min(xs)) + KDX
                if 0 <= ky < H and 0 <= kx < W and g[ky][kx] != BG:
                    ignore.add((ky, kx))
    out = [[BG] * W for _ in range(H)]
    ay, ax = ANCHOR
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if v == BG or (y, x) in ignore or v not in TABLE:
                continue
            col, pat = TABLE[v]
            for i in range(4):
                for j in range(4):
                    if pat[i][j]:
                        yy = y - ay + i
                        xx = x - ax + j
                        if 0 <= yy < H and 0 <= xx < W:
                            out[yy][xx] = col
    return out
''' % (bg, table, anchor, kdy, kdx)
    return src
