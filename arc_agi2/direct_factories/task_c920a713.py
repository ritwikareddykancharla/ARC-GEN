def build_program(d4, palette):
    # The mechanism is D4-invariant. Each box is an axis-aligned hollow rectangle,
    # and covered-by relations survive rotation and reflection. The output is a set
    # of concentric square rings, which every D4 element maps to itself. So the
    # emitted program works directly on visible coordinates without needing
    # orientation constants. The only specialised role is the background colour:
    # original colour 0 becomes palette[0].
    bg = int(palette[0])
    template = '''import numpy as np

BG = __BG__


def _frame_relations(g, bg):
    # For each colour, take the bounding box of its visible pixels. That is its
    # rectangle frame, because at least three corners always show. Collect every
    # other non-background colour lying on that frame; those colours sit above it.
    cols = sorted(int(c) for c in np.unique(g) if int(c) != bg)
    above = {}
    for c in cols:
        ys, xs = np.nonzero(g == c)
        y0, y1 = int(ys.min()), int(ys.max())
        x0, x1 = int(xs.min()), int(xs.max())
        border = np.concatenate([g[y0, x0:x1 + 1], g[y1, x0:x1 + 1],
                                 g[y0:y1 + 1, x0], g[y0:y1 + 1, x1]])
        above[c] = set(int(d) for d in np.unique(border)
                       if int(d) != c and int(d) != bg)
    return cols, above


def _score(order, above):
    pos = {c: i for i, c in enumerate(order)}
    s = 0
    for c in order:
        for d in above[c]:
            s += 1 if pos[d] > pos[c] else -1
    return s


def _hamiltonian_paths(cols, above, cap=20000):
    # Chains in which each next colour covers the previous one, visiting all colours.
    n = len(cols)
    found = []

    def dfs(path, used):
        if len(found) >= cap:
            return
        if len(path) == n:
            found.append(list(path))
            return
        for d in sorted(above[path[-1]]):
            if d not in used:
                path.append(d)
                used.add(d)
                dfs(path, used)
                path.pop()
                used.discard(d)

    for s in cols:
        dfs([s], {s})
    return found


def _greedy(cols, above):
    # Fallback: stacking order with the fewest violated covered-by relations.
    order = []
    remaining = set(cols)
    while remaining:
        best = None
        for c in sorted(remaining):
            v = sum(1 for b in remaining if b != c and c in above[b])
            if best is None or v < best[0]:
                best = (v, c)
        order.append(best[1])
        remaining.discard(best[1])
    return order


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    bg = BG
    cols, above = _frame_relations(g, bg)
    n = len(cols)
    if n == 0:
        return [[bg]]
    paths = _hamiltonian_paths(cols, above)
    if paths:
        order = max(paths, key=lambda p: _score(p, above))
    else:
        order = _greedy(cols, above)
    size = 2 * n - 1
    out = np.full((size, size), order[0], dtype=int)
    for i, c in enumerate(order[1:], start=1):
        out[i:size - i, i:size - i] = c
    return out.tolist()
'''
    return template.replace('__BG__', str(bg))
