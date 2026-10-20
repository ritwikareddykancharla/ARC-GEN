def build_program(d4, palette):
    floor = int(palette[0])
    wall = int(palette[5])
    src = '''from collections import deque

FLOOR = __FLOOR__
WALL = __WALL__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]
    # owner[y][x] holds the colour that claimed a cell; -1 means unclaimed.
    owner = [[-1] * W for _ in range(H)]
    q = deque()
    # Every cell that is neither floor nor wall is a seed.
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            if v != FLOOR and v != WALL:
                owner[y][x] = v
                q.append((y, x))
    # Grow all seeds at once with a 4-connected breadth-first flood over floor cells.
    # Walls block the flood. Edge-adjacent steps are kept the same under every D4 transform.
    while q:
        y, x = q.popleft()
        c = owner[y][x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W:
                if g[ny][nx] == FLOOR and owner[ny][nx] == -1:
                    owner[ny][nx] = c
                    out[ny][nx] = c
                    q.append((ny, nx))
    return out
'''
    return src.replace('__FLOOR__', str(floor)).replace('__WALL__', str(wall))
