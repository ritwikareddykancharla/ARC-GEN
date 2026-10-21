"""Direct visible-coordinate factory for ARC task 85fa5666.

Every 2x2 box (palette[2]) on background (palette[0]) has four diagonal corner
cells.  Corner colours move one step around the box (clockwise in visible
coordinates for d4 0-3, counter-clockwise for reflected d4 4-7) and each new
corner casts a diagonal ray away from the box until a box cell or the border.

Two stop details are not fixed by the constructor as a whole: its random path
always continues rays, while canonical train pair 2 (validate() extra_rows
patch) stops a ray that joins a same-coloured corner.  The emitted solver keeps
an explicit finite family of readings, keeps every reading that reproduces all
demonstrations exactly, and answers only when all surviving readings agree on
the full query output.  It raises instead of guessing when no reading survives
or survivors disagree (an episode-level ambiguity that must be gated upstream).
"""

TEMPLATE = """import numpy as np

BG = __BG__
BOX = __BOX__
CLOCKWISE = __CW__
ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))
# (obstacle_stop, join_mode): obstacle_stop=True stops a ray at any non-background
# cell (another box's corner); False passes over it.  join_mode None never joins,
# 'join' stops after painting a cell orthogonally next to a same-coloured corner
# whose own ray has a first free cell, 'graze' additionally requires that the
# next diagonal step clips a box cell.
HYPOTHESES = tuple((o, j) for o in (False, True) for j in (None, 'join', 'graze'))


def _blocks(g):
    H, W = g.shape
    seen = np.zeros((H, W), dtype=bool)
    found = []
    for y in range(H):
        for x in range(W):
            if g[y, x] != BOX or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ORTHO:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < H and 0 <= nx < W and not seen[ny, nx] and g[ny, nx] == BOX:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            if len(cells) == 4 and max(ys) - min(ys) == 1 and max(xs) - min(xs) == 1:
                found.append((min(ys), min(xs)))
    return found


def _plans(g):
    H, W = g.shape
    if CLOCKWISE:
        src = {'TR': 'TL', 'BR': 'TR', 'BL': 'BR', 'TL': 'BL'}
    else:
        src = {'TL': 'TR', 'TR': 'BR', 'BR': 'BL', 'BL': 'TL'}
    plans = []
    for y0, x0 in _blocks(g):
        pos = {'TL': (y0 - 1, x0 - 1, -1, -1), 'TR': (y0 - 1, x0 + 2, -1, 1),
               'BR': (y0 + 2, x0 + 2, 1, 1), 'BL': (y0 + 2, x0 - 1, 1, -1)}
        for k in ('TL', 'TR', 'BR', 'BL'):
            y, x, dy, dx = pos[k]
            sy, sx = pos[src[k]][0], pos[src[k]][1]
            if not (0 <= y < H and 0 <= x < W and 0 <= sy < H and 0 <= sx < W):
                continue
            c = int(g[sy, sx])
            if c == BG or c == BOX:
                continue
            plans.append((y, x, dy, dx, c))
    return plans


def _render(g, obstacle_stop, join_mode):
    H, W = g.shape
    inside = lambda y, x: 0 <= y < H and 0 <= x < W
    plans = _plans(g)
    joinable = {}
    for y, x, dy, dx, c in plans:
        if inside(y + dy, x + dx) and g[y + dy, x + dx] == BG:
            joinable[(y, x)] = c
    out = g.copy()
    for y, x, dy, dx, c in plans:
        yy, xx = y + dy, x + dx
        while inside(yy, xx):
            v = int(g[yy, xx])
            if v == BOX:
                break
            if v != BG:
                if obstacle_stop:
                    break
                yy += dy
                xx += dx
                continue
            out[yy, xx] = c
            if join_mode is not None:
                touch = any((yy + a, xx + b) != (y, x) and joinable.get((yy + a, xx + b)) == c
                            for a, b in ORTHO)
                if touch and join_mode == 'graze':
                    touch = ((inside(yy + dy, xx) and g[yy + dy, xx] == BOX) or
                             (inside(yy, xx + dx) and g[yy, xx + dx] == BOX))
                if touch:
                    break
            yy += dy
            xx += dx
    for y, x, dy, dx, c in plans:
        out[y, x] = c
    return out


def _grid(a):
    g = np.array(a, dtype=int)
    if g.ndim != 2 or g.size == 0:
        raise ValueError('85fa5666: grid must be a non-empty rectangle')
    return g


def solve(demonstrations, grid):
    q = _grid(grid)
    pairs = []
    for d in demonstrations:
        pairs.append((_grid(d['input']), _grid(d['output'])))
    if not pairs:
        raise ValueError('85fa5666: no demonstrations')
    survivors = []
    for obstacle_stop, join_mode in HYPOTHESES:
        if all(i.shape == o.shape and np.array_equal(_render(i, obstacle_stop, join_mode), o)
               for i, o in pairs):
            survivors.append((obstacle_stop, join_mode))
    if not survivors:
        raise ValueError('85fa5666: no reading reproduces every demonstration')
    answers = {}
    for h in survivors:
        r = _render(q, *h)
        answers[r.tobytes()] = r
    if len(answers) != 1:
        raise ValueError('85fa5666: demonstrations leave the query ambiguous: ' + repr(survivors))
    return next(iter(answers.values())).tolist()
"""


def build_program(d4, palette):
    src = TEMPLATE.replace('__BG__', str(int(palette[0])))
    src = src.replace('__BOX__', str(int(palette[2])))
    src = src.replace('__CW__', 'True' if int(d4) % 8 < 4 else 'False')
    return src
