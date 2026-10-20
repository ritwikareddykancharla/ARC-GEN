def build_program(d4, palette):
    pal = list(palette)
    BG = int(pal[7])
    WALL = int(pal[6])
    ITEM = int(pal[9])
    RING = int(pal[3])
    CORE = int(pal[2])
    k = int(d4) % 4
    flip = int(d4) >= 4

    def tf(dr, dc):
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return (dr, dc)

    order = [tf(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]

    src = '''from collections import deque

BG = %d
WALL = %d
ITEM = %d
RING = %d
CORE = %d
CAPACITY = 9
# The tank's fill order, as offsets from the core cell in visible coordinates.
FILL_ORDER = %r
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _find_core(g, H, W):
    best = None
    best_score = -1
    for r in range(H):
        for c in range(W):
            if g[r][c] != CORE:
                continue
            score = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W and g[rr][cc] == RING:
                        score += 1
            if score > best_score:
                best_score = score
                best = (r, c)
    return best


def solve(demonstrations, grid):
    g = [list(map(int, row)) for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    core = _find_core(g, H, W)
    if core is None:
        return g
    cy, cx = core
    tank = [(cy + dr, cx + dc) for dr, dc in FILL_ORDER]
    tank_in = [p for p in tank if 0 <= p[0] < H and 0 <= p[1] < W]
    tank_set = set(tank_in)
    dist = {}
    dq = deque()
    for p in tank_in:
        dist[p] = 0
        dq.append(p)
    while dq:
        r, c = dq.popleft()
        for dr, dc in STEPS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < H and 0 <= nc < W and (nr, nc) not in dist:
                if g[nr][nc] != WALL:
                    dist[(nr, nc)] = dist[(r, c)] + 1
                    dq.append((nr, nc))
    reached = sorted((d, p) for p, d in dist.items()
                     if p not in tank_set and g[p[0]][p[1]] == ITEM)
    taken = [p for _, p in reached[:CAPACITY]]
    out = [row[:] for row in g]
    for r, c in taken:
        out[r][c] = BG
    for r, c in tank[:len(taken)]:
        if 0 <= r < H and 0 <= c < W:
            out[r][c] = ITEM
    return out
''' % (BG, WALL, ITEM, RING, CORE, order)
    return src
