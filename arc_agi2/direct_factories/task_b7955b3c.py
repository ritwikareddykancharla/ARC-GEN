"""Remove plus stamps and restore the layered rectangles beneath (b7955b3c).

Every generator-valid reading of the visible query is enumerated. A reading
chooses the background colour (any non-plus colour, visible or unseen); every
other visible colour is then a box equal to its visible bounding box, with the
stacking order forced by which colour is visible inside each overlap. All
valid readings must render the same full output grid, otherwise solve raises.
There is no frequency vote, tie-break, D4 choice or fallback output.
"""
TEMPLATE = '''PLUS = __PLUS__
COLOURS = [c for c in range(10) if c != PLUS]


def _check_grid(grid):
    g = [[int(v) for v in row] for row in grid]
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        raise ValueError('Expected rectangular grid')
    return g


def _cells(g):
    cells = {}
    for r, row in enumerate(g):
        for k, v in enumerate(row):
            if v != PLUS:
                cells.setdefault(v, []).append((r, k))
    return cells


def _reading(g, cells, boxes, bg):
    """Render one reading, or return None when it violates a generator rule."""
    H, W = len(g), len(g[0])
    rects = {}
    for c in boxes:
        rs = [p[0] for p in cells[c]]
        ks = [p[1] for p in cells[c]]
        r0, r1, c0, c1 = min(rs), max(rs), min(ks), max(ks)
        # Box extents are drawn from 1..H-2 and 1..W-2.
        if r1 - r0 + 1 > H - 2 or c1 - c0 + 1 > W - 2:
            return None
        # At least three of the four corner checks show the box colour.
        if sum(g[r][k] == c for r in (r0, r1) for k in (c0, c1)) < 3:
            return None
        rects[c] = (r0, c0, r1, c1)
    below = {c: set() for c in boxes}
    for i, a in enumerate(boxes):
        ra = rects[a]
        for b in boxes[i + 1:]:
            rb = rects[b]
            t, l = max(ra[0], rb[0]), max(ra[1], rb[1])
            u, d = min(ra[2], rb[2]), min(ra[3], rb[3])
            if t > u or l > d:
                continue
            seen_a = any(t <= r <= u and l <= k <= d for r, k in cells[a])
            seen_b = any(t <= r <= u and l <= k <= d for r, k in cells[b])
            # The later box shows in the overlap; the earlier one cannot.
            if seen_a == seen_b:
                return None
            if seen_a:
                below[a].add(b)
            else:
                below[b].add(a)
    order, done, left = [], set(), list(boxes)
    while left:
        ready = [c for c in left if below[c] <= done]
        if not ready:
            return None
        order.extend(ready)
        done.update(ready)
        left = [c for c in left if c not in done]
    out = [[bg] * W for _ in range(H)]
    for c in order:
        r0, c0, r1, c1 = rects[c]
        for r in range(r0, r1 + 1):
            for k in range(c0, c1 + 1):
                out[r][k] = c
    for r in range(H):
        for k in range(W):
            if g[r][k] != PLUS and g[r][k] != out[r][k]:
                return None
    return out


def _outputs(g):
    cells = _cells(g)
    visible = sorted(cells)
    if any(c not in COLOURS for c in visible):
        raise ValueError('Unexpected colour')
    results = set()
    for bg in COLOURS:
        boxes = [c for c in visible if c != bg]
        out = _reading(g, cells, boxes, bg)
        if out is not None:
            results.add(tuple(tuple(row) for row in out))
    return results


def solve(demonstrations, grid):
    # Demonstrations only confirm the rule; they never select a reading.
    for pair in demonstrations:
        din = _check_grid(pair['input'])
        dout = tuple(tuple(row) for row in _check_grid(pair['output']))
        if dout not in _outputs(din):
            raise ValueError('Demonstration contradicts plus-removal rule')
    g = _check_grid(grid)
    outs = _outputs(g)
    if len(outs) != 1:
        raise ValueError('Query not identified: %d distinct valid readings' % len(outs))
    return [list(row) for row in outs.pop()]
'''


def build_program(d4, palette):
    # Rectangles, bounding boxes, containment and the H-2/W-2 extent limits
    # are all D4-equivariant, so d4 selects nothing. The only role constant
    # is the plus colour.
    return TEMPLATE.replace('__PLUS__', str(int(palette[8])))
