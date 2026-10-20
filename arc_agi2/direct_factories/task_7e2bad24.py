TEMPLATE = '''import numpy as np

# Colour roles are palette substitutions of the original roles:
#   BEAM = palette[1] (the diagonal beam)
#   MIRROR = palette[2] (a reflecting line)
#   GLASS = palette[3] (a transparent line that the beam paints over)
BEAM = @BEAM@
MIRROR = @MIRROR@
GLASS = @GLASS@

# Rival reflection readings. They take the same path on every interior mirror
# hit, on every glass crossing and at every border exit. They differ only when
# the beam makes corner contact with the END of a mirror line.
#   side        : flip the across-wall component when the cell orthogonally
#                 beside the beam (across the wall axis) is a mirror
#   either      : flip when that side cell OR the diagonal target is a mirror
#   target      : react only when the diagonal target is a mirror (rule text
#                 and archived solver); side cell -> flip dy, other side ->
#                 flip dx, corner-on -> reverse both
#   target_axis : diagonal target is a mirror -> flip the across-wall component
RULES = ('side', 'either', 'target', 'target_axis')


def _inb(H, W, y, x):
    return 0 <= y < H and 0 <= x < W


def _is_mirror(g, y, x):
    H, W = g.shape
    return _inb(H, W, y, x) and int(g[y, x]) == MIRROR


def _wall_axis(g):
    # Walls are parallel straight lines of length >= 4. Wall cells never touch
    # across the wall direction, so the direction in which they touch is the
    # wall axis.
    H, W = g.shape
    wall = (g == MIRROR) | (g == GLASS)
    hp = int(np.sum(wall[:, 1:] & wall[:, :-1])) if W > 1 else 0
    vp = int(np.sum(wall[1:, :] & wall[:-1, :])) if H > 1 else 0
    if hp > vp:
        return 'h'
    if vp > hp:
        return 'v'
    return None


def _step_target(g, axis, rule, y, x, dy, dx):
    H, W = g.shape
    for _ in range(4):
        ny, nx = y + dy, x + dx
        if not _inb(H, W, ny, nx):
            return None
        if int(g[ny, nx]) != MIRROR:
            return ny, nx, dy, dx
        if rule == 'target_axis' and axis == 'h':
            dy = -dy
        elif rule == 'target_axis' and axis == 'v':
            dx = -dx
        elif _is_mirror(g, y + dy, x):
            dy = -dy
        elif _is_mirror(g, y, x + dx):
            dx = -dx
        else:
            dy, dx = -dy, -dx
    return None


def _step_side(g, axis, rule, y, x, dy, dx):
    H, W = g.shape
    if axis is None:
        raise ValueError('Unresolved wall axis')
    if axis == 'h':
        if not 0 <= y + dy < H:
            return None
        hit = _is_mirror(g, y + dy, x)
    else:
        if not 0 <= x + dx < W:
            return None
        hit = _is_mirror(g, y, x + dx)
    if rule == 'either' and _is_mirror(g, y + dy, x + dx):
        hit = True
    if hit:
        if axis == 'h':
            dy = -dy
        else:
            dx = -dx
    ny, nx = y + dy, x + dx
    if not _inb(H, W, ny, nx):
        return None
    return ny, nx, dy, dx


def _trace(g, axis, rule, y, x, dy, dx, limit=None):
    H, W = g.shape
    cap = 4 * H * W + 16 if limit is None else limit
    path = [(y, x)]
    seen = {(y, x, dy, dx)}
    while len(path) < cap:
        if rule in ('side', 'either'):
            s = _step_side(g, axis, rule, y, x, dy, dx)
        else:
            s = _step_target(g, axis, rule, y, x, dy, dx)
        if s is None:
            break
        y, x, dy, dx = s
        if (y, x, dy, dx) in seen:
            break
        seen.add((y, x, dy, dx))
        path.append((y, x))
    return path


def _chain(g):
    # The visible beam is a simple diagonal chain, possibly bent by a
    # reflection. Return its cells in order from one end to the other.
    ys, xs = np.nonzero(g == BEAM)
    cells = set(zip(ys.tolist(), xs.tolist()))
    if not cells:
        return None

    def nbs(p):
        return [(p[0] + a, p[1] + b) for a in (-1, 1) for b in (-1, 1)
                if (p[0] + a, p[1] + b) in cells]

    if len(cells) == 1:
        return [next(iter(cells))]
    if any(len(nbs(p)) > 2 for p in cells):
        return None
    ends = sorted(p for p in cells if len(nbs(p)) == 1)
    if len(ends) != 2:
        return None
    order, prev, cur = [ends[0]], None, ends[0]
    while True:
        nxt = [q for q in nbs(cur) if q != prev]
        if not nxt:
            break
        prev, cur = cur, nxt[0]
        order.append(cur)
        if len(order) > len(cells):
            return None
    if len(order) != len(cells):
        return None
    return order


def _starts(g, order):
    # Extend from BOTH open ends. The tail's continuation always leaves the
    # grid immediately, so no head/tail tie-break is needed.
    H, W = g.shape
    if len(order) == 1:
        y, x = order[0]
        dirs = [(a, b) for a in (-1, 1) for b in (-1, 1)
                if _inb(H, W, y + a, x + b) and not _inb(H, W, y - a, x - b)]
        return [(y, x, a, b) for a, b in dirs] if len(dirs) == 1 else []
    a, b = order[0], order[1]
    c, d = order[-1], order[-2]
    return [(a[0], a[1], a[0] - b[0], a[1] - b[1]),
            (c[0], c[1], c[0] - d[0], c[1] - d[1])]


def _predict(g, rule):
    g = np.asarray(g, dtype=int)
    out = g.copy()
    order = _chain(g)
    if order is None or len(order)<3:
        raise ValueError('Expected a visible diagonal beam chain of length at least three')
    axis = _wall_axis(g)
    if axis is None:raise ValueError('Unresolved wall axis')
    for y, x, dy, dx in _starts(g, order):
        for py, px in _trace(g, axis, rule, y, x, dy, dx):
            out[py, px] = BEAM
    return out


def _chain_ok(g, rule):
    # Visible-input evidence: replaying the rule from the tail (the end whose
    # backward continuation leaves the grid) must reproduce any bend that is
    # already shown in the input.
    g = np.asarray(g, dtype=int)
    order = _chain(g)
    if order is None or len(order) < 3:
        return False
    H, W = g.shape
    behind_out = []
    for seq in (order, order[::-1]):
        e, n = seq[0], seq[1]
        behind_out.append(not _inb(H, W, 2 * e[0] - n[0], 2 * e[1] - n[1]))
    if behind_out[0] == behind_out[1]:
        return False
    seq = order if behind_out[0] else order[::-1]
    e, n = seq[0], seq[1]
    path = _trace(g, _wall_axis(g), rule, e[0], e[1], n[0] - e[0], n[1] - e[1],
                  limit=len(seq))
    return path == list(seq)


def _pairs(demonstrations):
    res = []
    for d in demonstrations or []:
        try:
            if isinstance(d, dict):
                a, b = d['input'], d['output']
            else:
                a, b = d[0], d[1]
            a = np.array(a, dtype=int)
            b = np.array(b, dtype=int)
        except Exception as exc:
            raise ValueError('Invalid demonstration') from exc
        if a.ndim != 2 or b.ndim != 2:raise ValueError('Invalid demonstration shape')
        res.append((a,b))
    return res


def analyse(demonstrations, grid):
    # Identifiability check that uses only demo pairs and the query input.
    g = np.array(grid, dtype=int)
    pairs = _pairs(demonstrations)
    if not pairs:raise ValueError('Demonstrations required')
    alive = []
    for rule in RULES:
        ok = _chain_ok(g, rule) and all(_chain_ok(a, rule) for a, _ in pairs)
        if ok:
            for a, b in pairs:
                p = _predict(a, rule)
                if p.shape != b.shape or not np.array_equal(p, b):
                    ok = False
                    break
        if ok:
            alive.append(rule)
    if not alive:raise ValueError('No endpoint interpretation fits visible evidence')
    pool = alive
    preds = {rule: _predict(g, rule) for rule in pool}
    first = preds[pool[0]]
    identifiable = all(np.array_equal(first, preds[r]) for r in pool)
    return {'alive': alive, 'preds': preds, 'identifiable': identifiable}


def solve(demonstrations, grid):
    info = analyse(demonstrations, grid)
    preds = info['preds']
    if not info['identifiable']:raise ValueError('Unresolved mirror-end interpretation')
    return next(iter(preds.values())).tolist()

'''


def build_program(d4, palette):
    # Orientation is read from pixels: the wall axis per grid, and the beam
    # direction from its visible chain. Fixture pairs mix wall orientations
    # inside one episode, so d4 cannot fix the axis. Only colour roles are
    # specialised here.
    pal = [int(v) for v in palette]
    src = TEMPLATE.replace('@BEAM@', str(pal[1]))
    src = src.replace('@MIRROR@', str(pal[2]))
    src = src.replace('@GLASS@', str(pal[3]))
    return src
