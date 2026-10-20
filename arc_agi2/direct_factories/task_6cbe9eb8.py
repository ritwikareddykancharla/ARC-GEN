def build_program(d4, palette):
    # The generator nests every rectangle in the BOTTOM-LEFT corner of its container.
    # Track where that corner lands in visible coordinates under the D4 transform.
    # cy: 0 = top, 1 = bottom. cx: 0 = left, 1 = right.
    cy, cx = 1, 0
    if d4 >= 4:
        cx = 1 - cx  # reversing each row swaps left and right
    for _ in range(d4 % 4):
        # one clockwise turn: TL->TR->BR->BL->TL
        cy, cx = cx, 1 - cy
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = __BG__
CY = __CY__
CX = __CX__


def _ncomp(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, bool)
    n = 0
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                n += 1
                seen[y, x] = True
                dq = deque([(y, x)])
                while dq:
                    a, b = dq.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = a + dy, b + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            dq.append((ny, nx))
    return n


def _bbox(g, c):
    ys, xs = np.where(g == c)
    return int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())


def _ring_mask(h, w):
    m = np.zeros((h, w), bool)
    m[0, :] = True
    m[-1, :] = True
    m[:, 0] = True
    m[:, -1] = True
    return m


def _classify(g):
    cols = [int(c) for c in np.unique(g)]
    comps = {c: _ncomp(g == c) for c in cols}
    boxes = {c: _bbox(g, c) for c in cols}
    # Object pieces: a later rectangle meets an earlier ring in one arc.
    # A later HOLLOW frame can cut it twice, because its interior leaves the ring visible.
    # With at most 4 objects, a ring has at most 4 pieces; solids stay connected.
    # Every object is at least 2 cells in each direction.
    texture = set()
    for c in cols:
        y0, x0, y1, x1 = boxes[c]
        if comps[c] > 4 or y1 - y0 < 1 or x1 - x0 < 1:
            texture.add(c)
    # Object pixels are only ever overwritten by later objects, never by texture.
    # So a colour whose ring (for ring-like colours) or whole box (for solids)
    # shows a texture colour cannot be an object.
    changed = True
    while changed:
        changed = False
        for c in cols:
            if c in texture:
                continue
            y0, x0, y1, x1 = boxes[c]
            region = g[y0:y1 + 1, x0:x1 + 1]
            own = region == c
            ring = _ring_mask(region.shape[0], region.shape[1])
            if np.all((~own) | ring):
                seen = region[ring]
            else:
                seen = region.ravel()
            if set(int(v) for v in np.unique(seen)) & texture:
                texture.add(c)
                changed = True
    objects = [c for c in cols if c not in texture]
    return objects, texture, boxes


def _is_frame(g, c, box, texture, objset, boxes):
    y0, x0, y1, x1 = box
    h, w = y1 - y0 + 1, x1 - x0 + 1
    if h < 5 or w < 5:
        return False
    inner = g[y0 + 1:y1, x0 + 1:x1]
    if (inner == c).any():
        return False
    vals = set(int(v) for v in np.unique(inner))
    if vals & texture:
        return True
    if len(vals) >= 2:
        return True
    i = next(iter(vals))
    if i in objset:
        return boxes[i] == (y0 + 1, x0 + 1, y1 - 1, x1 - 1)
    return True


def _place(ry0, rx0, ry1, rx1, h, w):
    if CY == 1:
        oy1 = ry1
        oy0 = ry1 - h + 1
    else:
        oy0 = ry0
        oy1 = ry0 + h - 1
    if CX == 1:
        ox1 = rx1
        ox0 = rx1 - w + 1
    else:
        ox0 = rx0
        ox1 = rx0 + w - 1
    return oy0, ox0, oy1, ox1


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    objects, texture, boxes = _classify(g)
    if not objects:
        return [list(map(int, r)) for r in g]
    objset = set(objects)
    items = []
    for c in objects:
        y0, x0, y1, x1 = boxes[c]
        h, w = y1 - y0 + 1, x1 - x0 + 1
        fr = _is_frame(g, c, boxes[c], texture, objset, boxes)
        items.append((h * w, min(h, w), c, h, w, fr))
    items.sort(key=lambda t: (-t[0], -t[1], t[2]))
    _, _, c, H, W, fr = items[0]
    out = np.full((H, W), BG, dtype=int)
    reg = (0, 0, H - 1, W - 1)
    for (_, _, c, h, w, fr) in items:
        ry0, rx0, ry1, rx1 = reg
        oy0, ox0, oy1, ox1 = _place(ry0, rx0, ry1, rx1, h, w)
        oy0 = max(oy0, 0)
        ox0 = max(ox0, 0)
        oy1 = min(oy1, H - 1)
        ox1 = min(ox1, W - 1)
        if oy1 < oy0 or ox1 < ox0:
            continue
        if fr:
            out[oy0, ox0:ox1 + 1] = c
            out[oy1, ox0:ox1 + 1] = c
            out[oy0:oy1 + 1, ox0] = c
            out[oy0:oy1 + 1, ox1] = c
            reg = (oy0 + 1, ox0 + 1, oy1 - 1, ox1 - 1)
        else:
            out[oy0:oy1 + 1, ox0:ox1 + 1] = c
            reg = (oy0, ox0, oy1, ox1)
    return [list(map(int, r)) for r in out]
'''
    src = src.replace('__BG__', str(bg)).replace('__CY__', str(int(cy))).replace('__CX__', str(int(cx)))
    return src
