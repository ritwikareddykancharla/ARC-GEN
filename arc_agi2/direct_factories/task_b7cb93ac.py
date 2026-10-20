def build_program(d4, palette):
    d4 = int(d4) % 8
    k = d4 % 4
    refl = d4 >= 4
    # Direction that means 'further left' in the original input frame, carried into visible coordinates.
    vr, vc = 0, -1
    if refl:
        vr, vc = 0, 1
    for _ in range(k):
        vr, vc = vc, -vr
    if k % 2 == 0:
        oh, ow = 3, 4
    else:
        oh, ow = 4, 3
    bg = int(palette[0])
    src = TEMPLATE
    src = src.replace('@BG@', repr(bg))
    src = src.replace('@OH@', repr(oh))
    src = src.replace('@OW@', repr(ow))
    src = src.replace('@VR@', repr(vr))
    src = src.replace('@VC@', repr(vc))
    return src


TEMPLATE = '''import numpy as np

BG = @BG@
OH = @OH@
OW = @OW@
VR = @VR@
VC = @VC@


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rot(cells):
    return _norm([(c, -r) for r, c in cells])


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for r in range(h):
        for c in range(w):
            if g[r, c] == BG or seen[r, c]:
                continue
            col = int(g[r, c])
            seen[r, c] = True
            stack = [(r, c)]
            cells = []
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and int(g[ny, nx]) == col:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            out.append((col, cells))
    return out


def solve(demonstrations, grid):
    g = np.asarray(grid, dtype=int)
    comps = _components(g)
    # Group identical pieces (same colour and same visible shape).
    keys = []
    members = []
    for col, cells in comps:
        key = (col, _norm(cells))
        if key in keys:
            members[keys.index(key)].append(cells)
        else:
            keys.append(key)
            members.append([cells])
    types = []
    for (col, shape), mem in zip(keys, members):
        orients = []
        cur = shape
        for _ in range(4):
            if cur not in [o for o, _ in orients]:
                orients.append((cur, 0 if cur == shape else 1))
            cur = _rot(cur)
        proj = max(min(VR * y + VC * x for y, x in cells) for cells in mem)
        types.append((col, orients, len(mem), proj))
    fallback = [[BG] * OW for _ in range(OH)]
    if sum(len(c) for _, c in comps) != OH * OW or not types:
        return fallback

    board = [[-1] * OW for _ in range(OH)]
    left = [t[2] for t in types]
    stack = []
    best = [10 ** 9]
    found = []

    def first_empty():
        for r in range(OH):
            row = board[r]
            for c in range(OW):
                if row[c] < 0:
                    return r, c
        return None

    def rec(cost):
        if cost > best[0]:
            return
        e = first_empty()
        if e is None:
            if cost < best[0]:
                best[0] = cost
                del found[:]
            found.append(list(stack))
            return
        er, ec = e
        for ti in range(len(types)):
            if not left[ti]:
                continue
            col = types[ti][0]
            for shape, oc in types[ti][1]:
                ar, ac = shape[0]
                dr, dc = er - ar, ec - ac
                cs = [(a + dr, b + dc) for a, b in shape]
                ok = True
                for y, x in cs:
                    if not (0 <= y < OH and 0 <= x < OW) or board[y][x] >= 0:
                        ok = False
                        break
                if not ok:
                    continue
                for y, x in cs:
                    board[y][x] = col
                left[ti] -= 1
                stack.append((ti, cs, oc))
                rec(cost + oc)
                stack.pop()
                left[ti] += 1
                for y, x in cs:
                    board[y][x] = -1

    rec(0)
    if not found:
        return fallback

    def paint(tiling):
        out = [[BG] * OW for _ in range(OH)]
        for ti, cs, _ in tiling:
            for y, x in cs:
                out[y][x] = types[ti][0]
        return out

    paintings = []
    for t in found:
        p = paint(t)
        if p not in paintings:
            paintings.append(p)
    if len(paintings) == 1:
        return paintings[0]

    # Swap tie: the piece lying further in the original 'left' direction stays unrotated.
    order = sorted(range(len(types)), key=lambda i: (-types[i][3], i))

    def tkey(tiling):
        cnt = [0] * len(types)
        for ti, _, oc in tiling:
            if oc == 0:
                cnt[ti] += 1
        return tuple(cnt[i] for i in order)

    best_t = found[0]
    best_k = tkey(best_t)
    for t in found[1:]:
        kk = tkey(t)
        if kk > best_k:
            best_k = kk
            best_t = t
    return paint(best_t)
'''
