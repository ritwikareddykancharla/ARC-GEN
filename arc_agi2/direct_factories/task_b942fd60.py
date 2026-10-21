def build_program(d4, palette):
    bg = int(palette[0])
    red = int(palette[2])
    # Native frame: the red seed sits on the left edge and fires rightward (0, 1).
    dr, dc = 0, 1
    if d4 >= 4:
        # Reversing each row moves the seed to the right edge, firing leftward.
        dr, dc = 0, -1
    for _ in range(d4 % 4):
        # A clockwise grid rotation maps direction (dr, dc) to (dc, -dr).
        dr, dc = dc, -dr
    template = """import numpy as np

BG = __BG__
RED = __RED__


def _pair(d):
    if isinstance(d, dict):
        return d.get('input'), d.get('output')
    return d[0], d[1]


def _seed(g):
    H, W = g.shape
    ys, xs = np.nonzero(g == RED)
    cells = list(zip(ys.tolist(), xs.tolist()))
    if len(cells) != 1:
        raise ValueError('Expected one ray seed')
    y, x = cells[0]
    dirs = []
    if x == 0: dirs.append((0,1))
    if x == W-1: dirs.append((0,-1))
    if y == 0: dirs.append((1,0))
    if y == H-1: dirs.append((-1,0))
    if len(dirs) != 1:
        raise ValueError('Seed must identify exactly one inward direction')
    return y, x, dirs[0][0], dirs[0][1]


def _trace(g, k):
    # A ray paints background red and passes over red. It ends at the grid
    # edge. When the next cell is an obstacle, it splits into the two
    # perpendicular directions if it is the seed ray or has moved >= k cells.
    # Each (cell, direction) start state is traced once, so the result does
    # not depend on processing order.
    H, W = g.shape
    out = g.copy()
    seed = _seed(g)
    start = seed
    seen = {start}
    stack = [(*seed, True)]
    while stack:
        r, c, dr, dc, first = stack.pop()
        out[r, c] = RED
        steps = 0
        while True:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= H or nc < 0 or nc >= W:
                break
            v = int(g[nr, nc])
            if v != BG and v != RED:
                if first or steps >= k:
                    for pr, pc in ((dc, dr), (-dc, -dr)):
                        s = (r, c, pr, pc)
                        if s not in seen:
                            seen.add(s)
                            stack.append((r, c, pr, pc, False))
                break
            r, c = nr, nc
            steps += 1
            out[r, c] = RED
    return out


def _consistent(demos, k):
    for d in demos:
        try:
            a, b = _pair(d)
            a = np.array(a, dtype=int)
            b = np.array(b, dtype=int)
        except Exception:
            return False
        if a.ndim != 2 or a.shape != b.shape:
            return False
        if not np.array_equal(_trace(a, k), b):
            return False
    return True


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    demos = list(demonstrations or [])
    if not demos:
        raise ValueError('Demonstrations required for split threshold')
    dims = [max(g.shape)] + [max(np.array(_pair(d)[0]).shape) for d in demos]
    kmax = max(dims) + 1
    fits = [k for k in range(kmax+1) if _consistent(demos,k)]
    if not fits:
        raise ValueError('No demonstrated split threshold')
    predictions = [_trace(g,k) for k in fits]
    if not all(np.array_equal(predictions[0],o) for o in predictions[1:]):
        raise ValueError('Query branching threshold unresolved by demonstrations')
    return predictions[0].tolist()
"""
    src = template.replace('__BG__', str(bg))
    src = src.replace('__RED__', str(red))
    src = src.replace('__DR__', str(dr))
    src = src.replace('__DC__', str(dc))
    return src
