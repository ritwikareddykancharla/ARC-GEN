def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    fill = int(palette[4])
    src = '''import numpy as np

BG = __BG__
RED = __RED__
FILL = __FILL__


def _clusters(cells, thr):
    unseen = set(cells)
    out = []
    while unseen:
        s = min(unseen)
        unseen.discard(s)
        stack = [s]
        cl = [s]
        while stack:
            y, x = stack.pop()
            near = [p for p in unseen if abs(p[0] - y) <= thr and abs(p[1] - x) <= thr]
            for p in near:
                unseen.discard(p)
                stack.append(p)
                cl.append(p)
        out.append(cl)
    return out


def _bbox(cl):
    ys = [p[0] for p in cl]
    xs = [p[1] for p in cl]
    return (min(ys), min(xs), max(ys), max(xs))


def _has_bg(g, b):
    return bool((g[b[0]:b[2] + 1, b[1]:b[3] + 1] == BG).any())


def _near(a, b, thr):
    for p in a:
        for q in b:
            if abs(p[0] - q[0]) <= thr and abs(p[1] - q[1]) <= thr:
                return True
    return False


def _split(g, cl):
    # A genuine hidden rectangle never contains background cells. If a
    # distance-2 cluster spans background, rebuild it from 8-connected pieces,
    # merging only while the merged bounding box stays background-free.
    if not _has_bg(g, _bbox(cl)):
        return [cl]
    parts = _clusters(cl, 1)
    changed = True
    while changed:
        changed = False
        n = len(parts)
        for i in range(n):
            for j in range(i + 1, n):
                if _near(parts[i], parts[j], 2) and not _has_bg(g, _bbox(parts[i] + parts[j])):
                    parts[i] = parts[i] + parts[j]
                    del parts[j]
                    changed = True
                    break
            if changed:
                break
    return parts


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int).copy()
    reds = [(int(p[0]), int(p[1])) for p in np.argwhere(g == RED)]
    boxes = []
    for cl in _clusters(reds, 2):
        for part in _split(g, cl):
            boxes.append(_bbox(part))
    boxes.sort()
    for (y0, x0, y1, x1) in boxes:
        sub = g[y0:y1 + 1, x0:x1 + 1]
        mask = (sub != RED) & (sub != BG)
        if mask.any():
            sub[mask] = FILL
    return g.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__RED__', str(red)).replace('__FILL__', str(fill))
