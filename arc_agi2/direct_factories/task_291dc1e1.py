def build_program(d4, palette):
    d4 = int(d4) % 8
    pal = [int(palette[c]) for c in range(10)]

    def img(v):
        dr, dc = v
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return dr, dc

    er = img((1, 0))
    ec = img((0, 1))
    stack_axis = 0 if er[0] != 0 else 1
    stack_fwd = (er[0] + er[1]) > 0
    width_fwd = (ec[0] + ec[1]) > 0
    rot_odd = (d4 % 4) % 2 == 1
    mrot = 1 if d4 < 4 else -1

    template = '''import numpy as np

P0 = __P0__
P1 = __P1__
P2 = __P2__
BG = __BG__
ROT_ODD = __ROT_ODD__
MROT = __MROT__
STACK_AXIS = __STACK_AXIS__
STACK_FWD = __STACK_FWD__
WIDTH_FWD = __WIDTH_FWD__


def _runs(idx):
    groups = []
    for i in idx:
        i = int(i)
        if groups and groups[-1][1] == i - 1:
            groups[-1][1] = i
        else:
            groups.append([i, i])
    return groups


def _dist(run, p):
    return min(abs(run[0] - p), abs(run[1] - p))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    corners = [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]
    best = None
    for (r, c) in corners:
        score = 0
        if g[r, c] == P0:
            score += 1000
        score += max(int(np.sum(g[r, :] == P1)) + int(np.sum(g[:, c] == P2)),
                     int(np.sum(g[:, c] == P1)) + int(np.sum(g[r, :] == P2)))
        if best is None or score > best[0]:
            best = (score, r, c)
    _, cr, cc = best
    row_score = int(np.sum(g[cr, :] == P1)) + int(np.sum(g[:, cc] == P2))
    col_score = int(np.sum(g[:, cc] == P1)) + int(np.sum(g[cr, :] == P2))
    one_is_row = row_score >= col_score

    nb = g != BG
    nb[cr, :] = False
    nb[:, cc] = False

    if one_is_row:
        one_pos, two_pos = cr, cc
        lane_has = nb.any(axis=1)
    else:
        one_pos, two_pos = cc, cr
        lane_has = nb.any(axis=0)
    lanes = _runs(np.nonzero(lane_has)[0])
    lanes.sort(key=lambda run: _dist(run, one_pos))

    orig_vertical = (not one_is_row) != ROT_ODD
    blocks = []
    for a, b in lanes:
        if one_is_row:
            seg_has = nb[a:b + 1, :].any(axis=0)
        else:
            seg_has = nb[:, a:b + 1].any(axis=1)
        segs = _runs(np.nonzero(seg_has)[0])
        segs.sort(key=lambda run: _dist(run, two_pos))
        for s, e in segs:
            if one_is_row:
                blk = g[a:b + 1, s:e + 1]
            else:
                blk = g[s:e + 1, a:b + 1]
            if orig_vertical:
                blk = np.rot90(blk, MROT)
            blocks.append(np.array(blk, dtype=int))

    if not blocks:
        return [[BG]]
    thick = [bk.shape[STACK_AXIS] for bk in blocks]
    lens = [bk.shape[1 - STACK_AXIS] for bk in blocks]
    S = sum(thick)
    Wout = max(lens)
    if STACK_AXIS == 0:
        out = np.full((S, Wout), BG, dtype=int)
    else:
        out = np.full((Wout, S), BG, dtype=int)
    pos = 0
    for bk, t, L in zip(blocks, thick, lens):
        if STACK_FWD:
            st = pos
        else:
            st = S - pos - t
        if WIDTH_FWD:
            off = (Wout - L) // 2
        else:
            off = Wout - L - (Wout - L) // 2
        if STACK_AXIS == 0:
            out[st:st + t, off:off + L] = bk
        else:
            out[off:off + L, st:st + t] = bk
        pos += t
    return out.tolist()
'''
    prog = (template
            .replace('__P0__', str(pal[0]))
            .replace('__P1__', str(pal[1]))
            .replace('__P2__', str(pal[2]))
            .replace('__BG__', str(pal[8]))
            .replace('__ROT_ODD__', 'True' if rot_odd else 'False')
            .replace('__MROT__', str(mrot))
            .replace('__STACK_AXIS__', str(stack_axis))
            .replace('__STACK_FWD__', 'True' if stack_fwd else 'False')
            .replace('__WIDTH_FWD__', 'True' if width_fwd else 'False'))
    return prog
