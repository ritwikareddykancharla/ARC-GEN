def build_program(d4, palette):
    # Every geometric test in this mechanism is invariant under D4: orthogonal
    # arms, 3x3 boxes, Chebyshev touching, squared Euclidean distance, and the
    # 8-neighbour path-end rule. So d4 needs no axis or direction change.
    # Only the two fixed colour roles are respecialised: black (0) and grey (5).
    # Badge ring and centre colours are read from the pixels.
    bg = int(palette[0])
    grey = int(palette[5])
    template = '''import numpy as np

BG = __BG__
GREY = __GREY__


def _badges(src, h, w):
    nodes = []
    for r in range(h):
        for c in range(w):
            arms = [(rr, cc) for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if 0 <= rr < h and 0 <= cc < w]
            if len(arms) < 3:
                continue
            if len(set(src[rr][cc] for rr, cc in arms)) != 1:
                continue
            ring = src[arms[0][0]][arms[0][1]]
            ctr = src[r][c]
            if ring in (BG, GREY) or ctr in (BG, GREY):
                continue
            box = [(rr, cc) for rr in range(max(0, r - 1), min(h, r + 2))
                   for cc in range(max(0, c - 1), min(w, c + 2))]
            if any(src[rr][cc] not in (BG, ring, ctr) for rr, cc in box):
                continue
            mask = set(p for p in box if src[p[0]][p[1]] != BG)
            nodes.append((ring, ctr, (r, c), mask))
    return nodes


def _ends(road):
    ends = []
    for (r, c) in road:
        n = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                q = (r + dr, c + dc)
                if q not in road:
                    continue
                if dr and dc and ((r + dr, c) in road or (r, c + dc) in road):
                    continue
                n += 1
        if n == 1:
            ends.append((r, c))
    return ends


def solve(demonstrations, grid):
    src = [[int(v) for v in row] for row in np.asarray(grid).tolist()]
    h = len(src)
    w = len(src[0])
    nodes = _badges(src, h, w)
    rings = set(nd[0] for nd in nodes)
    road = set((r, c) for r in range(h) for c in range(w) if src[r][c] == GREY)
    ends = _ends(road)
    if len(ends) != 2:
        raise ValueError('path must have exactly two ends')
    picks = []
    for (r, c) in ends:
        cands = [i for i, nd in enumerate(nodes)
                 if nd[1] in rings and any(max(abs(r - rr), abs(c - cc)) == 1 for rr, cc in nd[3])]
        if not cands:
            raise ValueError('no eligible badge at a path end')
        dist = dict((i, (nodes[i][2][0] - r) ** 2 + (nodes[i][2][1] - c) ** 2) for i in cands)
        best = min(dist.values())
        picks.append([i for i in cands if dist[i] == best])
    pairs = set(tuple(sorted((i, j))) for i in picks[0] for j in picks[1] if i != j)
    if len(pairs) != 1:
        raise ValueError('selected pair is not unique')
    out = [row[:] for row in src]
    for nd in nodes:
        for rr, cc in nd[3]:
            out[rr][cc] = BG
    for idx in next(iter(pairs)):
        ring, ctr, centre, mask = nodes[idx]
        donors = [nd for nd in nodes if nd[0] == ctr]
        if len(donors) != 1:
            raise ValueError('pointer does not name exactly one ring')
        for rr, cc in mask:
            out[rr][cc] = src[rr][cc]
        out[centre[0]][centre[1]] = donors[0][1]
    return out
'''
    return template.replace('__BG__', repr(bg)).replace('__GREY__', repr(grey))
