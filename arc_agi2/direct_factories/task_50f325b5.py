PROGRAM = '''import numpy as np

TEMPLATE = __T__
GREEN = __G__


def _norm(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _variants(cells):
    out = []
    seen = set()
    for mirrored in (False, True):
        cur = [(r, -c) if mirrored else (r, c) for r, c in cells]
        for _ in range(4):
            cur = [(c, -r) for r, c in cur]
            n = _norm(cur)
            if n not in seen:
                seen.add(n)
                out.append((n, mirrored))
    return out


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    H, W = g.shape
    pts = [(int(r), int(c)) for r, c in np.argwhere(g == TEMPLATE)]
    if not pts:
        return out.tolist()
    gm = (g == GREEN)
    candidates = {}
    for v, mirrored in _variants(pts):
        vh = max(r for r, _ in v) + 1
        vw = max(c for _, c in v) + 1
        for y in range(H - vh + 1):
            for x in range(W - vw + 1):
                ok = True
                for r, c in v:
                    if not gm[y + r, x + c]:
                        ok = False
                        break
                if ok:
                    cells = tuple(sorted((y + r, x + c) for r, c in v))
                    if cells not in candidates or not mirrored:
                        candidates[cells] = mirrored
    cells = sorted(candidates)
    n = len(cells)
    if n == 0:
        return out.tolist()
    occ = [set(c) for c in cells]
    conflicts = []
    for i in range(n):
        m = 0
        for j in range(n):
            if occ[i] & occ[j]:
                m |= (1 << j)
        conflicts.append(m)
    if n > 40:
        chosen = 0
        used = set()
        order = sorted(range(n), key=lambda i: (int(candidates[cells[i]]), cells[i]))
        for i in order:
            if not (occ[i] & used):
                used |= occ[i]
                chosen |= (1 << i)
    else:
        memo = {}

        def pack(mask):
            if not mask:
                return ((0, 0), 0)
            if mask in memo:
                return memo[mask]
            i = 0
            while not (mask >> i) & 1:
                i += 1
            bit = 1 << i
            no_score, no_min = pack(mask & ~bit)
            sub_score, sub_min = pack(mask & ~conflicts[i])
            yes_score = (sub_score[0] + 1, sub_score[1] - int(candidates[cells[i]]))
            yes_min = sub_min | bit
            if yes_score > no_score:
                res = (yes_score, yes_min)
            elif yes_score < no_score:
                res = (no_score, no_min)
            else:
                res = (yes_score, min(yes_min, no_min))
            memo[mask] = res
            return res

        _, chosen = pack((1 << n) - 1)
    for i in range(n):
        if (chosen >> i) & 1:
            for y, x in cells[i]:
                out[y, x] = TEMPLATE
    return out.tolist()
'''


def build_program(d4, palette):
    tc = int(palette[8])
    gc = int(palette[3])
    return PROGRAM.replace('__T__', str(tc)).replace('__G__', str(gc))
