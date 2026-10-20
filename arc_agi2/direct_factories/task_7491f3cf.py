TEMPLATE = """import numpy as np
from collections import deque

VERTICAL = __VERTICAL__
REVERSE = __REVERSE__


def _comps(mask, diag):
    mask = np.asarray(mask, bool)
    h, w = mask.shape
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        steps = steps + [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    seen = np.zeros((h, w), bool)
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
                    for dy, dx in steps:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _panels(g):
    fc = g[0, 0]
    h, w = g.shape
    rows = [y for y in range(h) if np.all(g[y, :] == fc)]
    cols = [x for x in range(w) if np.all(g[:, x] == fc)]
    rsp = [(a + 1, b) for a, b in zip(rows, rows[1:]) if b - a > 1]
    csp = [(a + 1, b) for a, b in zip(cols, cols[1:]) if b - a > 1]
    if not rsp or not csp:
        return []
    if len(rsp) > len(csp):
        vert = True
    elif len(csp) > len(rsp):
        vert = False
    else:
        vert = VERTICAL
    if vert:
        c0, c1 = csp[0]
        return [(r0, r1, c0, c1) for r0, r1 in rsp]
    r0, r1 = rsp[0]
    return [(r0, r1, c0, c1) for c0, c1 in csp]


def _pair(d):
    if isinstance(d, dict):
        return d.get('input'), d.get('output')
    return d[0], d[1]


def _reverse(demos):
    votes = 0
    for d in (demos or []):
        try:
            a, b = _pair(d)
            a = np.array(a, dtype=int)
            b = np.array(b, dtype=int)
        except Exception:
            continue
        if a.ndim != 2 or a.shape != b.shape:
            continue
        boxes = _panels(a)
        if len(boxes) < 4:
            continue
        ch = [bool(np.any(a[r0:r1, c0:c1] != b[r0:r1, c0:c1])) for r0, r1, c0, c1 in boxes]
        if ch[-1] and not ch[0]:
            votes -= 1
        elif ch[0] and not ch[-1]:
            votes += 1
    if votes > 0:
        return True
    if votes < 0:
        return False
    return REVERSE


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    boxes = _panels(g)
    if len(boxes) < 4:
        return out.tolist()
    if _reverse(demonstrations):
        boxes = boxes[::-1]
    p1, p2, p3 = [g[r0:r1, c0:c1] for r0, r1, c0, c1 in boxes[:3]]
    tr0, tr1, tc0, tc1 = boxes[3]
    if not (p1.shape == p2.shape == p3.shape == (tr1 - tr0, tc1 - tc0)):
        return out.tolist()
    vals, cnts = np.unique(np.concatenate([p.ravel() for p in (p1, p2, p3)]), return_counts=True)
    bg = vals[int(np.argmax(cnts))]
    comps = _comps(p1 != bg, True)
    if not comps:
        return out.tolist()
    comps.sort(key=len, reverse=True)
    line = set(comps[0])
    dots = set(c for comp in comps[1:] for c in comp)
    H, W = p1.shape
    free = np.ones((H, W), bool)
    for y, x in line:
        free[y, x] = False
    for reg in _comps(free, False):
        src = p2 if any(c in dots for c in reg) else p3
        for y, x in reg:
            out[tr0 + y, tc0 + x] = src[y, x]
    for y, x in line:
        out[tr0 + y, tc0 + x] = p2[y, x] if p2[y, x] != bg else p3[y, x]
    return out.tolist()
"""


def build_program(d4, palette):
    k = int(d4) % 8
    rot = k % 4
    vertical = rot in (1, 3)
    if k < 4:
        reverse = rot in (2, 3)
    else:
        reverse = rot in (0, 1)
    return TEMPLATE.replace('__VERTICAL__', repr(vertical)).replace('__REVERSE__', repr(reverse))
