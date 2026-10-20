TEMPLATE = '''import heapq

WALL = __WALL__
END = __END__
BLOCK = __BLOCK__
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    ends = [(y, x) for y in range(H) for x in range(W) if g[y][x] == END]
    if len(ends) != 2:
        return [row[:] for row in g]
    a, b = ends

    def touches_block(y, x):
        for dy, dx in DIRS:
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == BLOCK:
                return True
        return False

    allowed = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] == WALL and not touches_block(y, x):
                allowed.add((y, x))
    allowed.add(a)
    allowed.add(b)

    start = (a[0], a[1], -1)
    costs = {start: (0, 0)}
    prev = {start: None}
    heap = [(0, 0, start)]
    end = None
    while heap:
        s, t, st = heapq.heappop(heap)
        if costs[st] != (s, t):
            continue
        y, x, d = st
        if (y, x) == b:
            end = st
            break
        for nd, (dy, dx) in enumerate(DIRS):
            p = (y + dy, x + dx)
            if p not in allowed:
                continue
            ns = (p[0], p[1], nd)
            c = (s + 1, t + (1 if (d != -1 and nd != d) else 0))
            if ns not in costs or c < costs[ns]:
                costs[ns] = c
                prev[ns] = st
                heapq.heappush(heap, (c[0], c[1], ns))
    out = [row[:] for row in g]
    if end is None:
        return out
    cur = end
    while cur is not None:
        out[cur[0]][cur[1]] = END
        cur = prev[cur]
    return out
'''


def build_program(d4, palette):
    wall = int(palette[8])
    endc = int(palette[9])
    block = int(palette[7])
    src = TEMPLATE.replace('__WALL__', str(wall))
    src = src.replace('__END__', str(endc))
    src = src.replace('__BLOCK__', str(block))
    return src
