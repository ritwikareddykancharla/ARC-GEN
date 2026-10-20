def build_program(d4, palette):
    vertical = (d4 % 4) in (1, 3)
    bg = int(palette[7])
    sep = int(palette[6])
    if vertical:
        length_expr = 'g.shape[0]'
        line_expr = 'g[i, :]'
        out_expr = 'g[idxs, :]'
        axis_note = '# Panels are stacked vertically: separators are full rows, strips are row bands.'
    else:
        length_expr = 'g.shape[1]'
        line_expr = 'g[:, i]'
        out_expr = 'g[:, idxs]'
        axis_note = '# Panels sit side by side: separators are full columns, strips are column bands.'
    src = '''import numpy as np

BG = __BG__
SEP = __SEP__
__AXIS_NOTE__

def _line_colour(vals):
    cnt = {}
    for v in vals:
        v = int(v)
        # Separator lines are excluded by panel bounds, not by banning their
        # colour from all objects: a supplied fixture uses that colour inside.
        if v != BG:
            cnt[v] = cnt.get(v, 0) + 1
    if not cnt:
        return None
    best = None
    for k in sorted(cnt):
        if best is None or cnt[k] > cnt[best]:
            best = k
    return best

def _runs(colours, lo, hi):
    runs = []
    for i in range(lo, hi):
        c = colours[i]
        if c is None:
            continue
        if runs and runs[-1][0] == c and runs[-1][2] == i - 1:
            runs[-1][2] = i
        else:
            runs.append([c, i, i])
    return runs

def _panels(g, L):
    seps = []
    for i in range(L):
        line = __LINE__
        if bool(np.all(line == SEP)):
            seps.append(i)
    bounds = []
    start = 0
    for s in seps + [L]:
        if s > start:
            bounds.append((start, s - 1))
        start = s + 1
    widths = set(b - a + 1 for a, b in bounds)
    if len(bounds) == 3 and len(widths) == 1:
        return bounds
    size = (L - 2) // 3
    return [(0, size - 1), (size + 1, 2 * size), (2 * size + 2, 3 * size + 1)]

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    L = __LEN__
    colours = []
    for i in range(L):
        line = __LINE__
        colours.append(_line_colour(line))
    panels = _panels(g, L)
    idxs = []
    for k, (a, b) in enumerate(panels):
        runs = _runs(colours, a, b + 1)
        if not runs:
            continue
        if k == 0:
            idxs.extend(range(a, runs[0][2] + 1))
        elif k == len(panels) - 1:
            idxs.extend(range(runs[-1][1], b + 1))
        else:
            r = runs[1] if len(runs) >= 3 else runs[len(runs) // 2]
            idxs.extend(range(r[1], r[2] + 1))
    if not idxs:
        return g.tolist()
    idxs = np.array(idxs, dtype=int)
    out = __OUT__
    return out.tolist()
'''
    src = src.replace('__BG__', str(bg)).replace('__SEP__', str(sep))
    src = src.replace('__AXIS_NOTE__', axis_note)
    src = src.replace('__LEN__', length_expr).replace('__LINE__', line_expr).replace('__OUT__', out_expr)
    return src
