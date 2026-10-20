def build_program(d4, palette):
    k = int(d4) % 4
    # Original gravity is 'down'. The optional row reversal (d4 >= 4) keeps vertical
    # motion vertical. Each clockwise rotation turns down -> left -> up -> right.
    gy, gx = [(1, 0), (0, -1), (-1, 0), (0, 1)][k]
    air = int(palette[7])
    template = '''from collections import deque

AIR = __AIR__
GY = __GY__
GX = __GX__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    if H == 0 or W == 0:
        return g

    def inside(y, x):
        return 0 <= y < H and 0 <= x < W

    def on_floor(y, x):
        # The floor line is the grid edge that lies in the gravity direction.
        return not inside(y + GY, x + GX)

    seen = [[False] * W for _ in range(H)]
    objs = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == AIR or seen[y][x]:
                continue
            col = g[y][x]
            seen[y][x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if inside(ny, nx) and not seen[ny][nx] and g[ny][nx] == col:
                        seen[ny][nx] = True
                        q.append((ny, nx))
            objs.append((col, cells))

    static = set()
    movers = []
    for col, cells in objs:
        if any(on_floor(y, x) for y, x in cells):
            static.update(cells)
        else:
            movers.append((col, cells))

    out = [row[:] for row in g]
    for col, cells in movers:
        for y, x in cells:
            out[y][x] = AIR
    occupied = set(static)
    # The deepest object along the gravity direction settles first.
    movers.sort(key=lambda m: -max(y * GY + x * GX for y, x in m[1]))

    def ok(cells, d):
        for y, x in cells:
            ny, nx = y + GY * d, x + GX * d
            if not inside(ny, nx) or on_floor(ny, nx):
                return False
            if (ny, nx) in occupied:
                return False
            if (ny + GY, nx + GX) in static:
                return False
        return True

    for col, cells in movers:
        d = 0
        while ok(cells, d + 1):
            d += 1
        for y, x in cells:
            ny, nx = y + GY * d, x + GX * d
            out[ny][nx] = col
            occupied.add((ny, nx))
    return out
'''
    return (template.replace('__AIR__', str(air))
                    .replace('__GY__', str(gy))
                    .replace('__GX__', str(gx)))
