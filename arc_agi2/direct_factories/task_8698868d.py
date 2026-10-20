PROGRAM = r'''
import numpy as np
from collections import Counter, deque


def _components(mask):
    mask = np.asarray(mask, dtype=bool)
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _bbox(cells):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    return min(ys), min(xs), max(ys), max(xs)


def _background(g):
    cnt = Counter(g.ravel().tolist())
    best = max(cnt.values())
    cands = sorted(c for c, v in cnt.items() if v == best)
    if len(cands) == 1:
        return cands[0]
    border = np.concatenate([g[0, :], g[-1, :], g[:, 0], g[:, -1]]).tolist()
    bc = Counter(border)
    return max(cands, key=lambda c: (bc.get(c, 0), -c))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = _background(g)
    comps = _components(g != bg)
    if not comps:
        return g.tolist()
    # The panel block is the largest 4-connected non-background object.
    block = max(comps, key=len)
    y0, x0, y1, x1 = _bbox(block)
    out = g[y0:y1 + 1, x0:x1 + 1].copy()
    # Panels are identified by their distinct colours; each panel square is
    # the bounding box of its colour inside the block (panel borders are solid).
    panels = []
    for c in sorted(set(out.ravel().tolist()) - {bg}):
        ys, xs = np.nonzero(out == c)
        py0, py1 = int(ys.min()), int(ys.max())
        px0, px1 = int(xs.min()), int(xs.max())
        region = out[py0:py1 + 1, px0:px1 + 1]
        n = len(_components(region == bg))
        panels.append((py0, px0, py1, px1, c, n))
    lookup = {}
    for (py0, px0, py1, px1, c, n) in sorted(panels):
        if n not in lookup:
            lookup[n] = (c, py0, px0, py1, px1)
    for (py0, px0, py1, px1, c, n) in panels:
        region = out[py0:py1 + 1, px0:px1 + 1]
        region[region == bg] = c
    oh, ow = out.shape
    for comp in comps:
        sy0, sx0, sy1, sx1 = _bbox(comp)
        # Anything lying inside the block rectangle belongs to the block:
        # the block itself, or a panel-colour cell cut off from the rest of
        # its panel by diagonally touching holes. Those are not loose shapes.
        if sy0 >= y0 and sy1 <= y1 and sx0 >= x0 and sx1 <= x1:
            continue
        h, w = sy1 - sy0 + 1, sx1 - sx0 + 1
        patch = np.full((h, w), bg, dtype=int)
        for (y, x) in comp:
            patch[y - sy0, x - sx0] = g[y, x]
        n = len(_components(patch == bg))
        if n not in lookup:
            continue
        c, py0, px0, py1, px1 = lookup[n]
        ph, pw = py1 - py0 + 1, px1 - px0 + 1
        oy, ox = py0 + (ph - h) // 2, px0 + (pw - w) // 2
        for yy in range(h):
            for xx in range(w):
                ty, tx = oy + yy, ox + xx
                if 0 <= ty < oh and 0 <= tx < ow:
                    v = int(patch[yy, xx])
                    out[ty, tx] = v if v != bg else c
    return out.tolist()
'''


def build_program(d4, palette):
    # The mechanism is isotropic and colour-role free: background, panels,
    # shapes and hole counts are all read from the visible pixels, so no
    # orientation- or palette-specific constants are needed.
    return PROGRAM
