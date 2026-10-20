def build_program(d4, palette):
    wall = int(palette[8])
    bg = int(palette[0])
    # Odd D4 indices swap the visible row and column axes. The canonical door test
    # checks 'walls left and right' first. In the visible frame that axis is
    # vertical when the axis is swapped. This order only matters for degenerate
    # cells, but it keeps the precedence faithful.
    swap = bool(d4 % 2 == 1)
    src = '''
WALL = %d
BG = %d
AXIS_SWAP = %r


def solve(demonstrations, grid):
    g = [list(map(int, r)) for r in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [r[:] for r in g]
    cols = sorted({v for row in g for v in row if v != WALL and v != BG})
    if not cols:
        return out
    col = cols[0]

    def isw(y, x):
        return 0 <= y < H and 0 <= x < W and g[y][x] == WALL

    # Doors: non-wall cells with wall on both opposite sides.
    door = {}
    for y in range(H):
        for x in range(W):
            if g[y][x] == WALL:
                continue
            lr = isw(y, x - 1) and isw(y, x + 1)
            ud = isw(y - 1, x) and isw(y + 1, x)
            if AXIS_SWAP:
                if ud:
                    door[(y, x)] = [(y, x - 1), (y, x + 1)]
                elif lr:
                    door[(y, x)] = [(y - 1, x), (y + 1, x)]
            else:
                if lr:
                    door[(y, x)] = [(y - 1, x), (y + 1, x)]
                elif ud:
                    door[(y, x)] = [(y, x - 1), (y, x + 1)]

    # Rooms: 4-connected non-wall, non-door regions.
    rid = {}
    rooms = []
    for y in range(H):
        for x in range(W):
            if g[y][x] == WALL or (y, x) in door or (y, x) in rid:
                continue
            idx = len(rooms)
            cells = [(y, x)]
            rid[(y, x)] = idx
            k = 0
            while k < len(cells):
                cy, cx = cells[k]
                k += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and g[ny][nx] != WALL and (ny, nx) not in door and (ny, nx) not in rid:
                        rid[(ny, nx)] = idx
                        cells.append((ny, nx))
            rooms.append(cells)

    # Bounding boxes of 8-connected wall structures.
    wboxes = []
    seen = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] != WALL or (y, x) in seen:
                continue
            seen.add((y, x))
            stack = [(y, x)]
            b = [y, x, y, x]
            while stack:
                cy, cx = stack.pop()
                if cy < b[0]: b[0] = cy
                if cx < b[1]: b[1] = cx
                if cy > b[2]: b[2] = cy
                if cx > b[3]: b[3] = cx
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == WALL and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            stack.append((ny, nx))
            wboxes.append(tuple(b))

    def enclosed(cells):
        for y0, x0, y1, x1 in wboxes:
            if all(y0 <= cy <= y1 and x0 <= cx <= x1 for cy, cx in cells):
                return True
        return False

    # Room graph via doors.
    adj = {i: [] for i in range(len(rooms))}
    for d in sorted(door):
        rs = [(rid[n], n) for n in door[d] if n in rid]
        if len(rs) == 2 and rs[0][0] != rs[1][0]:
            (a, ca), (b, cb) = rs
            adj[a].append((b, d, ca, cb))
            adj[b].append((a, d, cb, ca))

    coloured = sorted({rid[c] for c in rid if g[c[0]][c[1]] == col})
    if not coloured:
        return out
    start, goal = coloured[0], coloured[-1]
    prev = {start: None}
    q = [start]
    while q:
        nq = []
        for r in q:
            for b, d, ca, cb in adj[r]:
                if b not in prev:
                    prev[b] = (r, d, ca, cb)
                    nq.append(b)
        q = nq
    if goal not in prev:
        return out

    entries = {}
    doors_used = []
    order = [goal]
    r = goal
    while prev.get(r) is not None:
        a, d, ca, cb = prev[r]
        doors_used.append(d)
        entries.setdefault(a, []).append(ca)
        entries.setdefault(r, []).append(cb)
        r = a
        order.append(r)

    for r in reversed(order):
        cells = rooms[r]
        if r == start or r == goal or enclosed(cells):
            for cy, cx in cells:
                out[cy][cx] = col
        else:
            ent = entries.get(r, [])
            if not ent:
                continue
            ys = [c[0] for c in ent]
            xs = [c[1] for c in ent]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            for cy, cx in cells:
                if y0 <= cy <= y1 and x0 <= cx <= x1:
                    out[cy][cx] = col
    for dy_, dx_ in doors_used:
        out[dy_][dx_] = col
    return out
''' % (wall, bg, swap)
    return src
