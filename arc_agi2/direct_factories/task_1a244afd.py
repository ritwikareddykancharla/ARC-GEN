def build_program(d4, palette):
    BG = int(palette[8])
    BLUE = int(palette[1])
    PINK = int(palette[6])
    OUT = int(palette[7])
    REFL = 1 if d4 >= 4 else 0
    prog = '''import numpy as np

BG = %d
BLUE = %d
PINK = %d
OUT = %d
REFL = %d

def _match(blues, pinks):
    nb, npk = len(blues), len(pinks)
    b_to_p = [-1] * nb
    p_to_b = [-1] * npk
    for _ in range(nb + npk + 1):
        changed = False
        for i in range(npk):
            if p_to_b[i] != -1:
                continue
            cands = [j for j in range(nb) if b_to_p[j] == -1 and
                     (pinks[i][0] == blues[j][0] or pinks[i][1] == blues[j][1])]
            if len(cands) != 1:
                continue
            p_to_b[i] = cands[0]
            b_to_p[cands[0]] = i
            changed = True
        if not changed:
            break
    rem_b = [j for j in range(nb) if b_to_p[j] == -1]
    rem_p = [i for i in range(npk) if p_to_b[i] == -1]
    if rem_b and rem_p:
        cand = {}
        for j in rem_b:
            cand[j] = [i for i in rem_p if pinks[i][0] == blues[j][0] or pinks[i][1] == blues[j][1]]
        order = sorted(rem_b, key=lambda j: len(cand[j]))
        best = [None, None, float('inf')]
        def rec(k, used, cur, cnt, dist):
            key = (-cnt, dist)
            if k == len(order):
                if best[0] is None or key < (best[1], best[2]):
                    best[0] = dict(cur); best[1] = -cnt; best[2] = dist
                return
            j = order[k]
            for i in cand[j]:
                if i in used:
                    continue
                used.add(i); cur[j] = i
                d = abs(pinks[i][0] - blues[j][0]) + abs(pinks[i][1] - blues[j][1])
                rec(k + 1, used, cur, cnt + 1, dist + d)
                del cur[j]; used.discard(i)
            rec(k + 1, used, cur, cnt, dist)
        if len(order) <= 12:
            rec(0, set(), {}, 0, 0)
            if best[0]:
                for j, i in best[0].items():
                    b_to_p[j] = i
                    p_to_b[i] = j
    return b_to_p

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    blues = [(int(r), int(c)) for r, c in np.argwhere(g == BLUE)]
    pinks = [(int(r), int(c)) for r, c in np.argwhere(g == PINK)]
    b_to_p = _match(blues, pinks)
    out = g.copy()
    for (r, c) in pinks:
        out[r, c] = BG
    for j, i in enumerate(b_to_p):
        if i < 0:
            continue
        br, bc = blues[j]
        pr, pc = pinks[i]
        dy, dx = pr - br, pc - bc
        if REFL:
            ny, nx = br + dx, bc - dy
        else:
            ny, nx = br - dx, bc + dy
        if 0 <= ny < H and 0 <= nx < W:
            out[ny, nx] = OUT
    return out.tolist()
''' % (BG, BLUE, PINK, OUT, REFL)
    return prog
