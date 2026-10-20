def build_program(d4, palette):
    # Original geometry: umbrella apex at top, feet at bottom, lines run DOWN (+row).
    base = [(0, 0), (1, -1), (1, 0), (1, 1), (2, -2), (2, -1), (2, 1), (2, 2), (3, -3), (3, 3)]
    k = d4 % 4
    flip = d4 >= 4
    def tf(v):
        dr, dc = v
        if flip:
            dc = -dc
        for _ in range(k):
            dr, dc = dc, -dr
        return (dr, dc)
    offs = [tf(v) for v in base]
    dy, dx = tf((1, 0))
    bg_hint = int(palette[0])
    src = '''import numpy as np
from collections import Counter, deque

DY, DX = %d, %d
OFFS = %r
BG_HINT = %d

def _largest_component(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    best = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                q = deque([(y, x)])
                n = 0
                while q:
                    cy, cx = q.popleft()
                    n += 1
                    for ay, ax in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + ay, cx + ax
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                best = max(best, n)
    return best

def _has_umbrella(g, c):
    h, w = g.shape
    ys, xs = np.where(g == c)
    for y, x in zip(ys.tolist(), xs.tolist()):
        ok = True
        for oy, ox in OFFS:
            ny, nx = y + oy, x + ox
            if not (0 <= ny < h and 0 <= nx < w) or g[ny, nx] != c:
                ok = False
                break
        if ok:
            return True
    return False

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    cnt = Counter(g.ravel().tolist())
    bg = BG_HINT if cnt.get(BG_HINT, 0) * 2 >= g.size else cnt.most_common(1)[0][0]
    colours = sorted(c for c in cnt if c != bg)
    out = g.copy()
    if len(colours) < 2:
        return out.tolist()
    comp = {c: _largest_component(g == c) for c in colours}
    cands = [c for c in colours if _has_umbrella(g, c)]
    if not cands:
        cands = colours
    kite = max(cands, key=lambda c: (comp[c], cnt[c]))
    others = [c for c in colours if c != kite]
    dot = max(others, key=lambda c: (cnt[c], -c))
    ys, xs = np.where(g == kite)
    if DX == 0:
        for x in range(int(xs.min()), int(xs.max()) + 1):
            cy = ys[xs == x]
            if len(cy) == 0:
                continue
            if DY == 1:
                far = int(cy.max())
                if np.any(g[far + 1:, x] == dot):
                    out[far + 1:, x] = dot
            else:
                far = int(cy.min())
                if np.any(g[:far, x] == dot):
                    out[:far, x] = dot
    else:
        for y in range(int(ys.min()), int(ys.max()) + 1):
            cx = xs[ys == y]
            if len(cx) == 0:
                continue
            if DX == 1:
                far = int(cx.max())
                if np.any(g[y, far + 1:] == dot):
                    out[y, far + 1:] = dot
            else:
                far = int(cx.min())
                if np.any(g[y, :far] == dot):
                    out[y, :far] = dot
    return out.tolist()
''' % (dy, dx, offs, bg_hint)
    return src
