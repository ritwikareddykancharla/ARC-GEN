def build_program(d4, palette):
    # Colour roles come from the palette: background = palette[8], divider = palette[0].
    # d4 is deliberately not used. The candidate-mechanism family below is closed under
    # every D4 transform (all four visible slide directions, both visible panel orders,
    # and tie-free nearest-shift rules). So D4 never picks among rival explanations;
    # only the demonstrations do.
    bg = int(palette[8])
    div = int(palette[0])
    nl = chr(10)
    header = "BG = " + str(bg) + nl + "DIV = " + str(div) + nl
    body = '''
import numpy as np
from itertools import permutations


class _Ambiguous(Exception):
    pass


DIRS = ((0, -1), (0, 1), (-1, 0), (1, 0))
POLICIES = [("over",), ("under",), ("near",), ("axis",)] + [("dir", d) for d in DIRS]
ORDERS = ("panel_fwd", "panel_bwd", "size_desc", "size_asc")


def _spans(cuts, n):
    edges = [-1] + sorted(cuts) + [n]
    out = []
    for a, b in zip(edges, edges[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def _panels(g):
    H, W = g.shape
    rows = [r for r in range(H) if (g[r] == DIV).all()]
    cols = [c for c in range(W) if (g[:, c] == DIV).all()]
    ys = _spans(rows, H)
    xs = _spans(cols, W)
    boxes = [(y0, x0, y1, x1) for (y0, y1) in ys for (x0, x1) in xs]
    if len(boxes) != 3:
        raise _Ambiguous("Expected three panels")
    return boxes


def _comps(p):
    h, w = p.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            v = int(p[y, x])
            if v == BG or v == DIV or seen[y, x]:
                continue
            seen[y, x] = True
            stack = [(y, x)]
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and int(p[ny, nx]) == v:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            out.append(cells)
    return out


def _pieces(g):
    boxes = _panels(g)
    h = boxes[0][2] - boxes[0][0] + 1
    w = boxes[0][3] - boxes[0][1] + 1
    pieces = []
    for y0, x0, y1, x1 in boxes:
        p = g[y0:y1 + 1, x0:x1 + 1]
        if p.shape != (h,w):raise _Ambiguous("Unequal panel sizes")
        comps = _comps(p)
        if len(comps) != 2:raise _Ambiguous("Expected two components per panel")
        comps.sort(key=len, reverse=True)
        if len(comps) > 1 and len(comps[0]) == len(comps[1]):
            raise _Ambiguous("tied largest component inside a panel")
        pieces.append(tuple((y, x, int(p[y, x])) for y, x in comps[0] if y < h and x < w))
    return h, w, pieces


def _orders(pieces):
    n = len(pieces)
    idx = tuple(range(n))
    perms = list(permutations(idx))
    sizes = [len(c) for c in pieces]

    def mono(perm, desc):
        s = [sizes[i] for i in perm]
        if desc:
            return all(s[i] >= s[i + 1] for i in range(len(s) - 1))
        return all(s[i] <= s[i + 1] for i in range(len(s) - 1))

    return {
        "panel_fwd": [idx],
        "panel_bwd": [idx[::-1]],
        "size_desc": [p for p in perms if mono(p, True)],
        "size_asc": [p for p in perms if mono(p, False)],
    }


def _fits(cells, occ, h, w, dy, dx):
    for y, x, _ in cells:
        ny, nx = y + dy, x + dx
        if not (0 <= ny < h and 0 <= nx < w) or occ[ny, nx]:
            return False
    return True


def _choose(policy, cells, occ, h, w):
    # Shift 0 whenever the spot is free; otherwise resolve the collision per policy.
    # Returns None when the policy is undefined (no fit, or a distance tie).
    if _fits(cells, occ, h, w, 0, 0):
        return (0, 0)
    kind = policy[0]
    if kind == "dir":
        sy, sx = policy[1]
        for k in range(1, max(h, w) + 1):
            if _fits(cells, occ, h, w, sy * k, sx * k):
                return (sy * k, sx * k)
        return None
    best_d = None
    best = []
    for dy in range(-h, h + 1):
        for dx in range(-w, w + 1):
            if dy == 0 and dx == 0:
                continue
            if kind == "axis" and dy != 0 and dx != 0:
                continue
            if not _fits(cells, occ, h, w, dy, dx):
                continue
            d = abs(dy) + abs(dx)
            if best_d is None or d < best_d:
                best_d = d
                best = [(dy, dx)]
            elif d == best_d:
                best.append((dy, dx))
    if len(best) == 1:
        return best[0]
    return None


def _render(policy, perm, pieces, h, w):
    out = np.full((h, w), BG, dtype=int)
    occ = np.zeros((h, w), dtype=bool)
    kind = policy[0]
    for i in perm:
        cells = pieces[i]
        if kind == "over":
            for y, x, c in cells:
                out[y, x] = c
                occ[y, x] = True
            continue
        if kind == "under":
            for y, x, c in cells:
                if not occ[y, x]:
                    out[y, x] = c
                    occ[y, x] = True
            continue
        s = _choose(policy, cells, occ, h, w)
        if s is None:
            return None
        dy, dx = s
        for y, x, c in cells:
            out[y + dy, x + dx] = c
            occ[y + dy, x + dx] = True
    return out


def _candidate(perms, policy, pieces, h, w):
    # An order with size ties is defined only if every tie-consistent order agrees.
    res = None
    for perm in perms:
        o = _render(policy, perm, pieces, h, w)
        if o is None:
            return None
        if res is None:
            res = o
        elif not np.array_equal(res, o):
            return None
    return res


def _predict(g):
    h, w, pieces = _pieces(g)
    orders = _orders(pieces)
    preds = {}
    for on in ORDERS:
        for pol in POLICIES:
            preds[(on, pol)] = _candidate(orders[on], pol, pieces, h, w)
    return preds


def _pair(d):
    if isinstance(d, dict):
        return d["input"], d["output"]
    return d[0], d[1]


def solve(demonstrations, grid):
    if not demonstrations:raise ValueError("Demonstrations required")
    alive = set((on, pol) for on in ORDERS for pol in POLICIES)
    for d in demonstrations or []:
        inp, outp = _pair(d)
        try:
            preds = _predict(np.array(inp, dtype=int))
        except _Ambiguous as exc:
            raise ValueError("Invalid demonstration geometry") from exc
        target = np.array(outp, dtype=int)
        alive = set(k for k in alive if preds[k] is not None and preds[k].shape == target.shape and np.array_equal(preds[k], target))
    if not alive:
        raise ValueError("no candidate mechanism is consistent with the demonstrations")
    try:
        preds = _predict(np.array(grid, dtype=int))
    except _Ambiguous:
        raise ValueError("query has a tied largest component; not identifiable")
    outs = [preds[k] for k in alive]
    if any(o is None for o in outs):
        raise ValueError("a surviving mechanism is undefined on the query; not identifiable")
    first = outs[0]
    for o in outs[1:]:
        if not np.array_equal(first, o):
            raise ValueError("surviving mechanisms disagree on the query; not identifiable")
    return first.tolist()
'''
    return header + body
