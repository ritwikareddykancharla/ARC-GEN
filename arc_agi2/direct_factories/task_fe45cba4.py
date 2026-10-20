_TEMPLATE = '''import numpy as np
from collections import Counter, deque

# Visible direction (dr, dc) of the original 'left' direction: the side away
# from the socket edge, where the loose pieces lie.
VR = __VR__
VC = __VC__


def _components(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps = []
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
                comps.append(sorted(cells))
    return comps


def _depth(cell):
    # Coordinate that grows toward the socket edge (original column index).
    return -(VR * cell[0] + VC * cell[1])


def _order_key(cells):
    ps = [_depth(c) for c in cells]
    return (min(ps), -max(ps))


def _fit(g, bg, piece, sock):
    H, W = g.shape
    pset = set(piece)
    sset = set(sock)
    for dy in range(-H + 1, H):
        for dx in range(-W + 1, W):
            if dy == 0 and dx == 0:
                continue
            new = []
            ok = True
            for y, x in piece:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < H and 0 <= nx < W):
                    ok = False
                    break
                if (ny, nx) in sset:
                    ok = False
                    break
                if g[ny, nx] != bg and (ny, nx) not in pset:
                    ok = False
                    break
                new.append((ny, nx))
            if not ok:
                continue
            union = sset | set(new)
            ys = [c[0] for c in union]
            xs = [c[1] for c in union]
            area = (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
            if len(union) == area:
                return new
    return None


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    out = g.copy()
    for col in sorted(set(g.ravel().tolist()) - {bg}):
        comps = _components(g == col)
        if len(comps) != 2:
            continue
        piece, sock = sorted(comps, key=_order_key)
        new = _fit(g, bg, piece, sock)
        if new is None:
            continue
        for y, x in piece:
            out[y, x] = bg
        for y, x in new:
            out[y, x] = col
    return out.tolist()
'''


def build_program(d4, palette):
    # Original 'left' = (0, -1). Horizontal flip negates dc; each clockwise
    # rotation maps a vector (dr, dc) to (dc, -dr).
    vr, vc = 0, -1
    if d4 >= 4:
        vc = -vc
    for _ in range(d4 % 4):
        vr, vc = vc, -vr
    return _TEMPLATE.replace('__VR__', str(vr)).replace('__VC__', str(vc))
