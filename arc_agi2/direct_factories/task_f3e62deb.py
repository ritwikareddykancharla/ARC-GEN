def build_program(d4, palette):
    base = {3: (0, -1), 4: (1, 0), 6: (-1, 0), 8: (0, 1)}
    k = int(d4) % 4
    flip = int(d4) >= 4
    table = {}
    for c, (dy, dx) in base.items():
        if flip:
            dx = -dx
        for _ in range(k):
            dy, dx = dx, -dy
        table[int(palette[c])] = (int(dy), int(dx))
    bg = int(palette[0])
    template = '''import numpy as np
from collections import Counter

TABLE = __TABLE__
BG = __BG__


def _bg(g):
    vals = g.ravel().tolist()
    if BG in vals:
        return BG
    return int(Counter(vals).most_common(1)[0][0])


def _components(g, bg):
    H, W = g.shape
    seen = np.zeros((H, W), bool)
    comps = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != bg and not seen[y, x]:
                c = int(g[y, x])
                stack = [(y, x)]
                seen[y, x] = True
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == c:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                comps.append((c, cells))
    return comps


def _pair(d):
    if isinstance(d, dict):
        return d.get('input'), d.get('output')
    return d[0], d[1]


def _learn(demonstrations):
    learned = {}
    for d in demonstrations or []:
        try:
            i, o = _pair(d)
            a = np.array(i, int)
            b = np.array(o, int)
        except Exception:
            continue
        if a.ndim != 2 or a.shape != b.shape:
            continue
        bg = _bg(a)
        for c in set(a.ravel().tolist()) - {bg}:
            ia = np.argwhere(a == c)
            ib = np.argwhere(b == c)
            if len(ia) == 0 or len(ib) == 0:
                continue
            dy = int(ib[:, 0].min() - ia[:, 0].min())
            dx = int(ib[:, 1].min() - ia[:, 1].min())
            if dy and not dx:
                learned.setdefault(int(c), (1 if dy > 0 else -1, 0))
            elif dx and not dy:
                learned.setdefault(int(c), (0, 1 if dx > 0 else -1))
    return learned


def _direction(c, learned):
    if c in TABLE:
        return TABLE[c]
    if c in learned:
        return learned[c]
    used = set(TABLE.values()) | set(learned.values())
    for d in ((0, -1), (1, 0), (-1, 0), (0, 1)):
        if d not in used:
            return d
    return None


def solve(demonstrations, grid):
    g = np.array(grid, int)
    H, W = g.shape
    bg = _bg(g)
    comps = _components(g, bg)
    learned = None
    out = g.copy()
    for c, cells in comps:
        for y, x in cells:
            out[y, x] = bg
    for c, cells in comps:
        if c not in TABLE and learned is None:
            learned = _learn(demonstrations)
        d = _direction(c, learned or {})
        ys = [p[0] for p in cells]
        xs = [p[1] for p in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        sy = sx = 0
        if d is not None:
            dy, dx = d
            if dy < 0:
                sy = -y0
            elif dy > 0:
                sy = H - 1 - y1
            if dx < 0:
                sx = -x0
            elif dx > 0:
                sx = W - 1 - x1
        for y, x in cells:
            out[y + sy, x + sx] = c
    return out.tolist()
'''
    return template.replace('__TABLE__', repr(table)).replace('__BG__', repr(bg))
