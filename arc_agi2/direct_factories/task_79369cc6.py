def build_program(d4, palette):
    c4 = int(palette[4])
    c6 = int(palette[6])
    src = '''
FOUR = __C4__
SIX = __C6__


def _rot_cw(t):
    h = len(t)
    w = len(t[0])
    return tuple(tuple(t[h - 1 - j][i] for j in range(h)) for i in range(w))


def _mirror(t):
    return tuple(tuple(row[::-1]) for row in t)


def _orientations(m):
    res = []
    seen = set()
    t = m
    for _ in range(4):
        for cand in (t, _mirror(t)):
            if cand not in seen:
                seen.add(cand)
                res.append(cand)
        t = _rot_cw(t)
    return res


def solve(demonstrations, grid):
    g = [list(r) for r in grid]
    H = len(g)
    if H == 0:
        return g
    W = len(g[0])
    fours = [(y, x) for y in range(H) for x in range(W) if g[y][x] == FOUR]
    if not fours:
        return g
    y0 = min(p[0] for p in fours)
    y1 = max(p[0] for p in fours)
    x0 = min(p[1] for p in fours)
    x1 = max(p[1] for p in fours)
    motif = tuple(tuple(g[y][x] for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1))
    found = []
    for t in _orientations(motif):
        h = len(t)
        w = len(t[0])
        sixes = [(dy, dx) for dy in range(h) for dx in range(w) if t[dy][dx] == SIX]
        paint = [(dy, dx) for dy in range(h) for dx in range(w) if t[dy][dx] == FOUR]
        if not sixes or not paint:
            continue
        for y in range(-h + 1, H):
            for x in range(-w + 1, W):
                if y == y0 and x == x0 and t == motif:
                    continue
                ok = True
                for dy, dx in sixes:
                    yy = y + dy
                    xx = x + dx
                    if not (0 <= yy < H and 0 <= xx < W) or g[yy][xx] != SIX:
                        ok = False
                        break
                if not ok:
                    continue
                for dy, dx in paint:
                    yy = y + dy
                    xx = x + dx
                    if 0 <= yy < H and 0 <= xx < W and g[yy][xx] in (SIX, FOUR):
                        ok = False
                        break
                if ok:
                    found.append((y, x, paint))
    out = [row[:] for row in g]
    for y, x, paint in found:
        for dy, dx in paint:
            yy = y + dy
            xx = x + dx
            if 0 <= yy < H and 0 <= xx < W:
                out[yy][xx] = FOUR
    return out
'''
    return src.replace('__C4__', repr(c4)).replace('__C6__', repr(c6))
