def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import deque

BG = %d


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if g[y, x] != BG and not seen[y, x]:
                col = g[y, x]
                q = deque([(y, x)])
                seen[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and g[ny, nx] == col:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                comps.append(cells)
    return comps


def _min_gap(vals):
    s = sorted(vals)
    return min(b - a for a, b in zip(s, s[1:]))


def _predict(grid, rule):
    g = np.array(grid, dtype=int)
    hollow = []
    for cells in _components(g):
        ys = [c[0] for c in cells]
        xs = [c[1] for c in cells]
        y0, y1, x0, x1 = min(ys), max(ys), min(xs), max(xs)
        area = (y1 - y0 + 1) * (x1 - x0 + 1)
        if len(cells) < area:
            hollow.append((y0, x0, y1, x1))
    if len(hollow) < 2:
        raise ValueError('Expected at least two hollow frames')
    if any(y1-y0 != 3 or x1-x0 != 3 for y0,x0,y1,x1 in hollow):
        raise ValueError('Expected four-cell square frames')
    rows = [b[0] for b in hollow]
    cols = [b[1] for b in hollow]
    rg = _min_gap(rows)
    cg = _min_gap(cols)
    if rule.startswith('span'):
        rs, cs = max(rows)-min(rows), max(cols)-min(cols)
        vertical = rs > cs or (rs == cs and rule == 'span_rows')
    elif rg < 4 and cg > 4:
        vertical = False
    elif rg > 4 and cg < 4:
        vertical = True
    else:
        raise ValueError('No uniquely separated projection axis')
    if vertical:
        hollow.sort(key=lambda b: (b[0], b[1]))
    else:
        hollow.sort(key=lambda b: (b[1], b[0]))
    pieces = [g[b[0]:b[2] + 1, b[1]:b[3] + 1].copy() for b in hollow]
    if vertical:
        H = sum(p.shape[0] for p in pieces)
        W = max(p.shape[1] for p in pieces)
    else:
        H = max(p.shape[0] for p in pieces)
        W = sum(p.shape[1] for p in pieces)
    out = np.full((H, W), BG, dtype=int)
    pos = 0
    for p in pieces:
        h, w = p.shape
        if vertical:
            out[pos:pos + h, :w] = p
            pos += h
        else:
            out[:h, pos:pos + w] = p
            pos += w
    return out.tolist()


def solve(demonstrations, grid):
    if not demonstrations:
        raise ValueError('Demonstrations required')
    rules = [rule for rule in ('gap', 'span_rows', 'span_cols')
             if all(_predict(p['input'],rule) == p['output'] for p in demonstrations)]
    if not rules:
        raise ValueError('No spacing rule fits all demonstrations')
    predictions = [_predict(grid,rule) for rule in rules]
    if any(out != predictions[0] for out in predictions[1:]):
        raise ValueError('Demonstrations do not distinguish spacing rules for query')
    return predictions[0]
''' % bg
    return src
