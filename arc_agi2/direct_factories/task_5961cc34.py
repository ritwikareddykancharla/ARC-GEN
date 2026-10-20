def _map_dir(d, d4):
    dr, dc = d
    if d4 >= 4:
        dc = -dc
    for _ in range(d4 % 4):
        dr, dc = dc, -dr
    return (dr, dc)


_TEMPLATE = '''import numpy as np
from collections import deque

BG = __BG__
BLOB = __BLOB__
MARK = __MARK__
LAUNCH = __LAUNCH__
BEAM = __BEAM__
DEFAULT_FIRE = __FIRE__
NOTCH_EXIT = __NOTCH__
STEPS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(mask):
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
                    for dy, dx in STEPS4:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(sorted(cells))
    return out


def _exit_side(blob, bset, mark):
    y0 = min(p[0] for p in blob)
    y1 = max(p[0] for p in blob)
    x0 = min(p[1] for p in blob)
    x1 = max(p[1] for p in blob)
    in_cols = all(x0 <= x <= x1 for _, x in mark)
    in_rows = all(y0 <= y <= y1 for y, _ in mark)
    if in_cols and all(y < y0 for y, _ in mark):
        return (-1, 0)
    if in_cols and all(y > y1 for y, _ in mark):
        return (1, 0)
    if in_rows and all(x < x0 for _, x in mark):
        return (0, -1)
    if in_rows and all(x > x1 for _, x in mark):
        return (0, 1)
    if in_cols and in_rows:
        opens = [s for s in STEPS4
                 if all((y + s[0], x + s[1]) not in bset for y, x in mark)]
        if len(opens) == 1:
            return opens[0]
        return NOTCH_EXIT
    if all(y < y0 for y, _ in mark):
        return (-1, 0)
    if all(y > y1 for y, _ in mark):
        return (1, 0)
    if all(x < x0 for _, x in mark):
        return (0, -1)
    if all(x > x1 for _, x in mark):
        return (0, 1)
    cy = sum(y for y, _ in mark) / len(mark)
    cx = sum(x for _, x in mark) / len(mark)
    oy = (cy - (y0 + y1) / 2.0) / max(1.0, (y1 - y0 + 1) / 2.0)
    ox = (cx - (x0 + x1) / 2.0) / max(1.0, (x1 - x0 + 1) / 2.0)
    if abs(oy) >= abs(ox):
        return (-1, 0) if oy < 0 else (1, 0)
    return (0, -1) if ox < 0 else (0, 1)


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    locs = np.argwhere(g == LAUNCH)
    if len(locs) == 0:
        out[out != BEAM] = BG
        return out.tolist()
    fy, fx = int(locs[0][0]), int(locs[0][1])
    d = DEFAULT_FIRE
    for dy, dx in STEPS4:
        y, x = fy + dy, fx + dx
        if 0 <= y < H and 0 <= x < W and g[y, x] == BEAM:
            d = (-dy, -dx)
    out[fy, fx] = BEAM
    blobs = _components(g == BLOB)
    marks = _components(g == MARK)
    blob_id = {}
    for i, b in enumerate(blobs):
        for c in b:
            blob_id[c] = i
    front = [(fy, fx)]
    used = set()
    while True:
        hit = None
        while True:
            nxt = [(y + d[0], x + d[1]) for y, x in front]
            if any(not (0 <= y < H and 0 <= x < W) for y, x in nxt):
                break
            hs = [blob_id[c] for c in nxt if c in blob_id]
            if hs:
                hit = hs[0]
                break
            for y, x in nxt:
                out[y, x] = BEAM
            front = nxt
        if hit is None or hit in used:
            break
        used.add(hit)
        b = blobs[hit]
        for y, x in b:
            out[y, x] = BEAM
        bs = set(b)
        mk = None
        for m in marks:
            if any((y + a, x + c) in bs for y, x in m for a in (-1, 0, 1) for c in (-1, 0, 1)):
                mk = m
                break
        if mk is None:
            break
        for y, x in mk:
            out[y, x] = BEAM
        d = _exit_side(b, bs, mk)
        front = list(mk)
    out[out != BEAM] = BG
    return out.tolist()
'''


def build_program(d4, palette):
    p = [int(palette[i]) for i in range(10)]
    fire = _map_dir((-1, 0), int(d4))
    notch = _map_dir((0, 1), int(d4))
    src = _TEMPLATE
    for key, val in (('__BG__', p[8]), ('__BLOB__', p[1]), ('__MARK__', p[3]),
                     ('__LAUNCH__', p[4]), ('__BEAM__', p[2]),
                     ('__FIRE__', fire), ('__NOTCH__', notch)):
        src = src.replace(key, repr(val))
    return src
