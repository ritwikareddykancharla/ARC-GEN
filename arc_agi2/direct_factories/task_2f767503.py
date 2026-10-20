def build_program(d4, palette):
    bg = int(palette[7])
    blob = int(palette[4])
    bar = int(palette[5])
    gun = int(palette[9])
    src = '''from collections import deque

BG = __BG__
BLOB = __BLOB__
BAR = __BAR__
GUN = __GUN__


def _sign(v):
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


def solve(demonstrations, grid):
    g = [list(int(v) for v in row) for row in grid]
    H = len(g)
    if H == 0:
        return g
    W = len(g[0])
    nines = [(r, c) for r in range(H) for c in range(W) if g[r][c] == GUN]
    bars = [(r, c) for r in range(H) for c in range(W) if g[r][c] == BAR]
    if not nines or not bars:
        return g
    nr, nc = nines[0]
    # The bar cell orthogonally adjacent to the trigger is the bar centre.
    adj = [(r, c) for (r, c) in bars if abs(r - nr) + abs(c - nc) == 1]
    if adj:
        cr, cc = adj[0]
        dr, dc = cr - nr, cc - nc
    else:
        my = sum(p[0] for p in bars) / float(len(bars))
        mx = sum(p[1] for p in bars) / float(len(bars))
        dr, dc = _sign(my - nr), _sign(mx - nc)
        if dr != 0 and dc != 0:
            if abs(my - nr) >= abs(mx - nc):
                dc = 0
            else:
                dr = 0
    if dr == 0 and dc == 0:
        return g
    r, c = nr, nc
    while 0 <= r < H and 0 <= c < W:
        if g[r][c] == BLOB:
            # erase the whole 4-connected blob containing this ray cell
            q = deque([(r, c)])
            g[r][c] = BG
            while q:
                y, x = q.popleft()
                for ay, ax in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= ay < H and 0 <= ax < W and g[ay][ax] == BLOB:
                        g[ay][ax] = BG
                        q.append((ay, ax))
        r += dr
        c += dc
    return g
'''
    src = src.replace('__BG__', repr(bg)).replace('__BLOB__', repr(blob))
    src = src.replace('__BAR__', repr(bar)).replace('__GUN__', repr(gun))
    return src
