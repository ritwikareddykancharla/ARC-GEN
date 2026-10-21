TEMPLATE = '''import numpy as np

BG = __BG__
WALL = __WALL__
HALO = __HALO__
LINE = __LINE__
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _components(mask):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not seen[y, x]:
                seen[y, x] = True
                stack = [(y, x)]
                cells = []
                while stack:
                    cy, cx = stack.pop()
                    cells.append((cy, cx))
                    for dy, dx in N4:
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
                comps.append(cells)
    return comps


def _enclosed(cells, h, w):
    wall = np.zeros((h + 2, w + 2), dtype=bool)
    for y, x in cells:
        wall[y + 1, x + 1] = True
    ext = np.zeros_like(wall)
    ext[0, 0] = True
    stack = [(0, 0)]
    while stack:
        y, x = stack.pop()
        for dy, dx in N4:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h + 2 and 0 <= nx < w + 2 and not ext[ny, nx] and not wall[ny, nx]:
                ext[ny, nx] = True
                stack.append((ny, nx))
    return (~ext & ~wall)[1:h + 1, 1:w + 1]


def _full_rect(cells):
    if not cells:
        return None
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    box = (min(ys), min(xs), max(ys), max(xs))
    if (box[2] - box[0] + 1) * (box[3] - box[1] + 1) == len(set(cells)):
        return box
    return None


def _area(box):
    return (box[2] - box[0] + 1) * (box[3] - box[1] + 1)


def _decomposition(cells):
    whole = _full_rect(cells)
    if whole is not None:
        return [whole]
    y0 = min(c[0] for c in cells)
    y1 = max(c[0] for c in cells)
    x0 = min(c[1] for c in cells)
    x1 = max(c[1] for c in cells)
    options = []
    for k in range(x0 + 1, x1 + 1):
        a = _full_rect([c for c in cells if c[1] < k])
        b = _full_rect([c for c in cells if c[1] >= k])
        if a is not None and b is not None and a[3] + 1 == b[1] and a[0] <= b[2] and b[0] <= a[2]:
            options.append((a, b))
    for k in range(y0 + 1, y1 + 1):
        a = _full_rect([c for c in cells if c[0] < k])
        b = _full_rect([c for c in cells if c[0] >= k])
        if a is not None and b is not None and a[2] + 1 == b[0] and a[1] <= b[3] and b[1] <= a[3]:
            options.append((a, b))
    if len(options) == 1:
        return list(options[0])
    if len(options) == 2:
        m0 = min(_area(p) for p in options[0])
        m1 = min(_area(p) for p in options[1])
        if m0 < m1:
            return list(options[0])
        if m1 < m0:
            return list(options[1])
    return None


def _touch_lining(inner_cells, wall_set):
    out = set()
    for y, x in inner_cells:
        hit = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (y + dy, x + dx) in wall_set:
                    hit = True
        if hit:
            out.add((y, x))
    return out


def _piece_lining(inner_cells, wall_set):
    pieces = _decomposition(inner_cells)
    if pieces is None:
        raise ValueError('Closed outline has no unique native rectangle decomposition')
    out = set()
    for top, left, bottom, right in pieces:
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                if y == top or y == bottom or x == left or x == right:
                    out.add((y, x))
    return out


def _transform(grid, mode):
    g = np.asarray(grid, dtype=int)
    h, w = g.shape
    out = g.copy()
    linings = []
    for cells in _components(g == WALL):
        inner = _enclosed(cells, h, w)
        if not inner.any():
            continue
        inner_cells = [(int(p[0]), int(p[1])) for p in np.argwhere(inner)]
        wall_set = set(cells)
        for y, x in cells:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not inner[ny, nx] and g[ny, nx] == BG and out[ny, nx] == BG:
                        out[ny, nx] = HALO
        if mode == 'pieces':
            linings.append(_piece_lining(inner_cells, wall_set))
        else:
            linings.append(_touch_lining(inner_cells, wall_set))
    for lining in linings:
        for y, x in lining:
            if g[y, x] == BG:
                out[y, x] = LINE
    return out


def _pairs(demonstrations):
    pairs = []
    for d in demonstrations or []:
        if isinstance(d, dict):
            i, o = d.get('input'), d.get('output')
        elif isinstance(d, (list, tuple)) and len(d) >= 2:
            i, o = d[0], d[1]
        else:
            continue
        if i is None or o is None:
            continue
        pairs.append((i, o))
    return pairs


def _mismatch(mode, pairs):
    total = 0
    for i, o in pairs:
        try:
            pred = _transform(i, mode)
            exp = np.asarray(o, dtype=int)
        except Exception:
            return None
        if pred.shape != exp.shape:
            total += max(pred.size, exp.size)
        else:
            total += int((pred != exp).sum())
    return total


def solve(demonstrations, grid):
    pairs = _pairs(demonstrations)
    if not pairs: raise ValueError('Demonstrations required')
    modes = [m for m in ('pieces', 'touch') if _mismatch(m, pairs) == 0]
    if not modes: raise ValueError('Demonstrations contradict closed-outline rules')
    answers = {}
    for m in modes:
        result = _transform(grid, m)
        answers[result.tobytes()] = result
    if len(answers) != 1: raise ValueError('Demonstrations do not distinguish internal seam lining')
    result = next(iter(answers.values())).tolist()
    observed = {v for _, o in pairs for row in o for v in row} | {v for row in grid for v in row}
    if any(v not in observed for row in result for v in row):
        raise ValueError('Undemonstrated output colour')
    return result
'''


def build_program(d4, palette):
    pal = [int(v) for v in palette]
    src = TEMPLATE
    src = src.replace('__BG__', str(pal[0]))
    src = src.replace('__WALL__', str(pal[1]))
    src = src.replace('__HALO__', str(pal[2]))
    src = src.replace('__LINE__', str(pal[3]))
    return src
