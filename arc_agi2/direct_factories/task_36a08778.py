def build_program(d4, palette):
    bg = int(palette[7])
    wall = int(palette[2])
    flow = int(palette[6])
    gr, gc = 1, 0
    lr, lc = 0, 1
    if d4 >= 4:
        gc = -gc
        lc = -lc
    for _ in range(d4 % 4):
        gr, gc = gc, -gr
        lr, lc = lc, -lr
    gr = int(gr); gc = int(gc); lr = int(lr); lc = int(lc)
    if gr == 1:
        edge = '[(0, c) for c in range(W)]'
    elif gr == -1:
        edge = '[(H - 1, c) for c in range(W)]'
    elif gc == 1:
        edge = '[(r, 0) for r in range(H)]'
    else:
        edge = '[(r, W - 1) for r in range(H)]'
    template = '''from collections import deque

BG = __BG__
WALL = __WALL__
FLOW = __FLOW__
GR, GC = __GR__, __GC__
LR, LC = __LR__, __LC__


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    starts = []
    for (y, x) in __EDGE__:
        if g[y][x] != FLOW:
            continue
        while inb(y + GR, x + GC) and g[y + GR][x + GC] == FLOW:
            y += GR
            x += GC
        starts.append((y, x))
    q = deque(starts)
    seen = set()
    while q:
        y, x = q.popleft()
        if (y, x) in seen or not inb(y, x):
            continue
        seen.add((y, x))
        if g[y][x] == BG:
            g[y][x] = FLOW
        while inb(y + GR, x + GC) and g[y + GR][x + GC] != WALL:
            y += GR
            x += GC
            if g[y][x] == BG:
                g[y][x] = FLOW
        hy, hx = y + GR, x + GC
        if not inb(hy, hx):
            continue
        a = 0
        while inb(hy - (a + 1) * LR, hx - (a + 1) * LC) and g[hy - (a + 1) * LR][hx - (a + 1) * LC] == WALL:
            a += 1
        b = 0
        while inb(hy + (b + 1) * LR, hx + (b + 1) * LC) and g[hy + (b + 1) * LR][hx + (b + 1) * LC] == WALL:
            b += 1
        for t in range(-a - 1, b + 2):
            py, px = y + t * LR, x + t * LC
            if inb(py, px) and g[py][px] == BG:
                g[py][px] = FLOW
        for t in (-a - 1, b + 1):
            py, px = y + t * LR, x + t * LC
            if inb(py, px):
                q.append((py, px))
    return g
'''
    prog = template.replace('__BG__', str(bg)).replace('__WALL__', str(wall)).replace('__FLOW__', str(flow))
    prog = prog.replace('__GR__', str(gr)).replace('__GC__', str(gc)).replace('__LR__', str(lr)).replace('__LC__', str(lc))
    prog = prog.replace('__EDGE__', edge)
    return prog
