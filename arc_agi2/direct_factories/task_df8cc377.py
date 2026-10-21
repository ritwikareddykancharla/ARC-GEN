def build_program(d4, palette):
    # d4 is deliberately unused: it never selects the checkerboard phase.
    # The emitted program keeps every visible anchor-corner hypothesis that
    # reproduces ALL demonstrations and answers only if every surviving
    # (role reading, corner) hypothesis renders the identical query output.
    # The only specialised constant is the background colour palette[0].
    bg = int(palette[0])
    template = '''import numpy as np
from itertools import combinations

BG = __BG__
# (a, b): a = 1 anchors the checkerboard on the interior's bottom row (else top),
#         b = 1 anchors it on the interior's right column (else left).
CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))


def _box(g, c):
    # Colour c is frame-capable if its cells are exactly the border of its
    # bounding box (at least 3x3) and the ring just inside that border is
    # background (natively that ring is reserved, so no pixel can land there).
    ys, xs = np.nonzero(g == c)
    if ys.size == 0:
        return None
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    hh, ww = y1 - y0 + 1, x1 - x0 + 1
    if hh < 3 or ww < 3 or int(ys.size) != 2 * hh + 2 * ww - 4:
        return None
    sub = g[y0:y1 + 1, x0:x1 + 1]
    if not (np.all(sub[0] == c) and np.all(sub[-1] == c) and np.all(sub[:, 0] == c) and np.all(sub[:, -1] == c)):
        return None
    inner = sub[1:-1, 1:-1]
    if not (np.all(inner[0] == BG) and np.all(inner[-1] == BG) and np.all(inner[:, 0] == BG) and np.all(inner[:, -1] == BG)):
        return None
    return (y0, x0, y1, x1)


def _layout_ok(boxes, H, W):
    # Visible, D4-invariant constructor constraints.
    if len(boxes) != (2 if min(H, W) <= 20 else 3):
        return False
    for (y0, x0, y1, x1) in boxes:
        if y1 - y0 + 1 > H // 2 or x1 - x0 + 1 > W // 2:
            return False
    for i in range(len(boxes)):
        for j in range(i):
            p, q = boxes[i], boxes[j]
            if p[2] + 1 < q[0] or q[2] + 1 < p[0] or p[3] + 1 < q[1] or q[3] + 1 < p[1]:
                continue
            return False
    return True


def _readings(g):
    # Every role assignment consistent with the visible input: k frame colours,
    # k pixel colours, distinct ceil(area/2) needs equal to pixel counts.
    H, W = g.shape
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG})
    if len(colours) % 2:
        return []
    k = len(colours) // 2
    boxes = {}
    for c in colours:
        b = _box(g, c)
        if b is not None:
            boxes[c] = b
    counts = {c: int(np.count_nonzero(g == c)) for c in colours}
    out = []
    for S in combinations(sorted(boxes), k):
        P = tuple(c for c in colours if c not in S)
        need = {}
        for c in S:
            y0, x0, y1, x1 = boxes[c]
            need[c] = ((y1 - y0 - 1) * (x1 - x0 - 1) + 1) // 2
        nv = sorted(need.values())
        if len(set(nv)) != len(nv) or nv != sorted(counts[c] for c in P):
            continue
        if not _layout_ok([boxes[c] for c in S], H, W):
            continue
        by_count = {counts[c]: c for c in P}
        out.append((tuple((boxes[c], by_count[need[c]]) for c in S), P))
    return out


def _render(g, reading, corner):
    frames, pcols = reading
    out = g.copy()
    for c in pcols:
        out[g == c] = BG
    a, b = corner
    for (y0, x0, y1, x1), col in frames:
        h, w = y1 - y0 - 1, x1 - x0 - 1
        ph = (a * (h - 1) + b * (w - 1)) % 2
        for y in range(h):
            for x in range(w):
                out[y0 + 1 + y, x0 + 1 + x] = col if (y + x) % 2 == ph else BG
    return out


def _pair(d):
    if isinstance(d, dict):
        a, b = d['input'], d['output']
    else:
        a, b = d[0], d[1]
    a = np.array(a, dtype=int)
    b = np.array(b, dtype=int)
    if a.ndim != 2 or a.shape != b.shape:
        raise ValueError('bad demonstration')
    return a, b


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    corners = set(CORNERS)
    try:
        demos = [_pair(d) for d in (demonstrations or [])]
    except Exception:
        return None
    for di, do in demos:
        fits = set()
        for rd in _readings(di):
            for cn in CORNERS:
                if np.array_equal(_render(di, rd, cn), do):
                    fits.add(cn)
        # A demonstration that no hypothesis explains is a contradiction:
        # abstain rather than skip it.
        corners &= fits
        if not corners:
            return None
    readings = _readings(g)
    if not readings:
        return None
    outs = [_render(g, rd, cn) for rd in readings for cn in sorted(corners)]
    for o in outs[1:]:
        if not np.array_equal(o, outs[0]):
            # Rival visible explanations disagree on this query: abstain.
            return None
    return outs[0].tolist()
'''
    return template.replace('__BG__', str(bg))
