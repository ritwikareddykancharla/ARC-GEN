def build_program(d4, palette):
    bg = int(palette[7])
    sn = int(palette[3])
    mk = int(palette[0])
    gr = int(palette[5])
    src = '''BG = __BG__
SN = __SN__
MK = __MK__
GR = __GR__
DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def solve(demonstrations, grid):
    g = [[int(v) for v in row] for row in grid]
    H = len(g)
    W = len(g[0]) if H else 0
    out = [row[:] for row in g]

    def inb(r, c):
        return 0 <= r < H and 0 <= c < W

    def onb(r, c):
        return r == 0 or r == H - 1 or c == 0 or c == W - 1

    # Heads: snake cells on the border flanked along the border by two marker cells.
    heads = {}
    for r in range(H):
        for c in range(W):
            if g[r][c] != SN or not onb(r, c):
                continue
            if (r == 0 or r == H - 1) and H > 1 and 0 < c < W - 1 and g[r][c - 1] == MK and g[r][c + 1] == MK:
                heads[(r, c)] = (1 if r == 0 else -1, 0)
            elif (c == 0 or c == W - 1) and W > 1 and 0 < r < H - 1 and g[r - 1][c] == MK and g[r + 1][c] == MK:
                heads[(r, c)] = (0, 1 if c == 0 else -1)

    erase = set()
    place = []
    for (hr, hc), (dr, dc) in sorted(heads.items()):
        cr, cc = hr + dr, hc + dc
        if not inb(cr, cc) or g[cr][cc] != SN or (cr, cc) in heads:
            continue
        path = [(cr, cc)]
        seen = {(hr, hc), (cr, cc)}
        d = (dr, dc)
        while True:
            r, c = path[-1]
            cands = []
            for a, b in DIRS:
                nr, nc = r + a, c + b
                if inb(nr, nc) and g[nr][nc] == SN and (nr, nc) not in seen and (nr, nc) not in heads:
                    cands.append((nr, nc))
            if not cands:
                break
            st = (r + d[0], c + d[1])
            nxt = st if st in cands else cands[0]
            d = (nxt[0] - r, nxt[1] - c)
            seen.add(nxt)
            path.append(nxt)
        tr, tc = path[-1]
        # A full (untruncated) snake reaches the border and has its grey tail marker beside the tip.
        if len(path) < 2 or not onb(tr, tc):
            continue
        fives = [(tr + a, tc + b) for a, b in DIRS if inb(tr + a, tc + b) and g[tr + a][tc + b] == GR]
        if not fives:
            continue
        erase.update(path)
        erase.update(fives)
        place.append((cr, cc))
    for r, c in erase:
        out[r][c] = BG
    for r, c in place:
        out[r][c] = GR
    return out
'''
    return (src.replace('__BG__', str(bg))
               .replace('__SN__', str(sn))
               .replace('__MK__', str(mk))
               .replace('__GR__', str(gr)))
