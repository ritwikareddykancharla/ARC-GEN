_TEMPLATE = '''import numpy as np
from collections import Counter, deque

# Edge codes in VISIBLE coordinates: 0 = top, 1 = right, 2 = bottom, 3 = left.
# Shared-size objects slide to RISE_EDGE; unique-size objects slide to SINK_EDGE.
RISE_EDGE = __RISE__
SINK_EDGE = __SINK__


def _components(g, bg):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    objs = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != bg and not seen[y, x]:
                col = int(g[y, x])
                seen[y, x] = True
                q = deque([(y, x)])
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == col:
                                seen[ny, nx] = True
                                q.append((ny, nx))
                objs.append((col, cells))
    return objs


def _offset(cells, edge, H, W):
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    if edge == 0:
        return (-min(ys), 0)
    if edge == 2:
        return (H - 1 - max(ys), 0)
    if edge == 3:
        return (0, -min(xs))
    return (0, W - 1 - max(xs))


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    bg = int(Counter(g.ravel().tolist()).most_common(1)[0][0])
    objs = _components(g, bg)
    cnt = Counter(len(cells) for _, cells in objs)
    out = np.full_like(g, bg)
    ups = [o for o in objs if cnt[len(o[1])] > 1]
    downs = [o for o in objs if cnt[len(o[1])] == 1]
    for group, edge in ((ups, RISE_EDGE), (downs, SINK_EDGE)):
        for col, cells in group:
            dy, dx = _offset(cells, edge, H, W)
            for y, x in cells:
                out[y + dy, x + dx] = col
    return out.tolist()
'''


def build_program(d4, palette):
    # Original rise direction is 'up'. Reversing rows (d4>=4) keeps up as up.
    # Each clockwise rotation maps up->right->down->left.
    rise = int(d4) % 4
    sink = (rise + 2) % 4
    return _TEMPLATE.replace('__RISE__', str(rise)).replace('__SINK__', str(sink))
