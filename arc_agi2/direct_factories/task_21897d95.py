TEMPLATE = """import numpy as np
from collections import Counter, deque

# Marker colour of the T bars/stems (canonical colour 1 under the palette).
MARK = @MK@
# Preferred colour of the 5-cell corner (L) marker (canonical colour 9).
LCOL = @LC@
# Visible corner position of the L (sign dy, sign dx relative to its 3x3 box centre)
# -> np.rot90 k applied to the repainted grid, already expressed in visible coordinates.
TURN = @TURN@

STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _inb(H, W, y, x):
    return 0 <= y < H and 0 <= x < W


def _find_tees(g):
    H, W = g.shape
    tees = []
    for y in range(H):
        for x in range(W):
            for dy, dx in STEPS:
                py, px = dx, dy
                bar = [(y + py, x + px), (y - py, x - px)]
                stem = (y + dy, x + dx)
                if not all(_inb(H, W, a, b) for a, b in bar + [stem]):
                    continue
                if not all(g[a, b] == MARK for a, b in bar + [stem]):
                    continue
                by, bx = y - dy, x - dx
                if _inb(H, W, by, bx) and g[by, bx] == MARK:
                    continue
                corners = [(stem[0] + py, stem[1] + px), (stem[0] - py, stem[1] - px)]
                if not all(_inb(H, W, a, b) for a, b in corners):
                    continue
                if any(g[a, b] == MARK for a, b in corners):
                    continue
                owner = int(g[corners[0][0], corners[0][1]])
                paint = int(g[y, x]) if g[y, x] != MARK else owner
                tees.append({'cells': bar + [stem, (y, x)], 'owner': owner,
                             'paint': paint, 'target': (y + 2 * dy, x + 2 * dx)})
    return tees


def _components(mask):
    H, W = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in STEPS:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(cells)
    return out


def _find_corner_marker(g):
    cols = sorted(set(int(v) for v in g.ravel()) - {MARK}, key=lambda c: (c != LCOL, c))
    for col in cols:
        for cells in _components(g == col):
            if len(cells) != 5:
                continue
            ys = [p[0] for p in cells]
            xs = [p[1] for p in cells]
            y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
            if y1 - y0 != 2 or x1 - x0 != 2:
                continue
            s = set(cells)
            for cy in (y0, y1):
                for cx in (x0, x1):
                    if all((cy, xx) in s for xx in range(x0, x1 + 1)) and all((yy, cx) in s for yy in range(y0, y1 + 1)):
                        return s, (-1 if cy == y0 else 1, -1 if cx == x0 else 1)
    return None, None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    tees = _find_tees(g)
    lcells, corner = _find_corner_marker(g)
    c = g.copy()
    for t in tees:
        for a, b in t['cells']:
            c[a, b] = t['owner']
    if lcells:
        cnt = Counter()
        for y, x in lcells:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if _inb(H, W, yy, xx) and (yy, xx) not in lcells:
                        cnt[int(c[yy, xx])] += 1
        fill = cnt.most_common(1)[0][0] if cnt else int(c[next(iter(lcells))])
        for a, b in lcells:
            c[a, b] = fill
    out = c.copy()
    for t in tees:
        ty, tx = t['target']
        if not _inb(H, W, ty, tx):
            continue
        col = c[ty, tx]
        seen = {(ty, tx)}
        q = deque([(ty, tx)])
        while q:
            cy, cx = q.popleft()
            out[cy, cx] = t['paint']
            for dy, dx in STEPS:
                ny, nx = cy + dy, cx + dx
                if _inb(H, W, ny, nx) and (ny, nx) not in seen and c[ny, nx] == col:
                    seen.add((ny, nx))
                    q.append((ny, nx))
    if corner is not None:
        k = TURN.get(corner, 0)
        if k:
            out = np.rot90(out, k)
    return [[int(v) for v in row] for row in out]
"""


def build_program(d4, palette):
    d4 = int(d4) % 8
    mk = int(palette[1])
    lc = int(palette[9])
    # canonical L corner (sign dy, sign dx) -> np.rot90 k (TR: CCW, TL: CW; BL/BR as archived)
    canonical = {(-1, 1): 1, (-1, -1): -1, (1, -1): 1, (1, 1): -1}
    turn = {}
    for (dy, dx), k in canonical.items():
        vy, vx = dy, dx
        if d4 >= 4:
            vx = -vx
        for _ in range(d4 % 4):
            vy, vx = vx, -vy
        turn[(vy, vx)] = k if d4 < 4 else -k
    src = TEMPLATE
    src = src.replace('@MK@', repr(mk))
    src = src.replace('@LC@', repr(lc))
    src = src.replace('@TURN@', repr(turn))
    return src
