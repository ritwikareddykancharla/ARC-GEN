TEMPLATE = '''import numpy as np

BG = __BG__
GRAY = __GRAY__


def _comps(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                out.append(sorted(cells))
    return out


def _norm(cells):
    y0 = min(y for y, x in cells)
    x0 = min(x for y, x in cells)
    return tuple(sorted((y - y0, x - x0) for y, x in cells))


def _holes(g):
    # Hole = background cells strictly inside the bounding box of a gray component.
    holes = []
    for comp in _comps(g == GRAY):
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        if y1 - y0 < 2 or x1 - x0 < 2:
            continue
        cells = [(y, x) for y in range(y0 + 1, y1) for x in range(x0 + 1, x1)
                 if g[y, x] == BG]
        if cells:
            holes.append(cells)
    return holes


def _assignments(cands):
    found = []

    def rec(i, cur):
        if i == len(cands):
            found.append(tuple(cur))
            return
        for c in cands[i]:
            if c is not None and c in cur:
                continue
            cur.append(c)
            rec(i + 1, cur)
            cur.pop()

    rec(0, [])
    return found


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    holes = _holes(g)
    colours = sorted(set(int(v) for v in g.ravel().tolist()) - {BG, GRAY})
    pix = {}
    for c in colours:
        ys, xs = np.nonzero(g == c)
        pix[c] = [(int(y), int(x)) for y, x in zip(ys.tolist(), xs.tolist())]
    # A colour fits a hole iff its WHOLE pixel set is an exact translate of the hole.
    cands = []
    for hole in holes:
        hs = _norm(hole)
        opts = [c for c in colours if len(pix[c]) == len(hole) and _norm(pix[c]) == hs]
        cands.append(opts + [None])
    found = _assignments(cands)
    if not found:
        return out.tolist()
    most = max(sum(1 for c in a if c is not None) for a in found)
    best = [a for a in found if sum(1 for c in a if c is not None) == most]
    if len(best) != 1 or most != len(holes):
        raise ValueError("The visible shapes do not determine a unique complete assignment")
    choice = best[0]
    for c in choice:
        if c is not None:
            for y, x in pix[c]:
                out[y, x] = BG
    for hole, c in zip(holes, choice):
        if c is not None:
            for y, x in hole:
                out[y, x] = c
    return out.tolist()
'''


def build_program(d4, palette):
    # Matching uses exact translation only. A translate stays a translate under
    # every D4 transform, so no axis or direction needs specialising. Only the
    # colour roles (background = palette[0], gray = palette[5]) are baked in.
    bg = int(palette[0])
    gray = int(palette[5])
    return TEMPLATE.replace('__BG__', str(bg)).replace('__GRAY__', str(gray))
