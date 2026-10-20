def build_program(d4, palette):
    k = d4 % 4
    # Original family: lines are rows. Flip (d4>=4) keeps rows as rows; each
    # clockwise quarter-turn swaps rows<->columns. So odd k => lines are columns.
    axis = 1 if (k % 2 == 1) else 0
    bg = int(palette[0])
    # Edge where the partial prefixes start, in visible coordinates (informational).
    # Original prefixes start at the left edge.
    edge = 'left'
    if d4 >= 4:
        edge = 'right'
    order = ['top', 'right', 'bottom', 'left']
    for _ in range(k):
        edge = order[(order.index(edge) + 1) % 4] if edge != 'left' else 'top'
    src = '''import numpy as np

BG = __BG__
AXIS = __AXIS__  # 0: pattern lines are rows, 1: pattern lines are columns
PREFIX_EDGE = '__EDGE__'  # edge from which partial lines start (for reference)


def _num_lines(g):
    return g.shape[0] if AXIS == 0 else g.shape[1]


def _get(g, i):
    if AXIS == 0:
        return g[i, :]
    return g[:, i]


def _set(g, i, vals):
    if AXIS == 0:
        g[i, :] = vals
    else:
        g[:, i] = vals


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    out = g.copy()
    n = _num_lines(g)
    # Template: a line with no background cells; prefer one using exactly two colours.
    tmpl_i = None
    for i in range(n):
        line = _get(g, i)
        if np.all(line != BG) and len(set(line.tolist())) == 2:
            tmpl_i = i
            break
    if tmpl_i is None:
        for i in range(n):
            if np.all(_get(g, i) != BG):
                tmpl_i = i
                break
    if tmpl_i is None:
        return out.tolist()
    tmpl = _get(g, tmpl_i).tolist()
    for i in range(n):
        if i == tmpl_i:
            continue
        line = _get(g, i).tolist()
        if all(v == BG for v in line):
            continue
        mapping = {}
        for x, v in enumerate(line):
            if v != BG and tmpl[x] not in mapping:
                mapping[tmpl[x]] = v
        new = list(line)
        for x, t in enumerate(tmpl):
            if t in mapping:
                new[x] = mapping[t]
        _set(out, i, new)
    return out.tolist()
'''
    return src.replace('__BG__', str(bg)).replace('__AXIS__', str(axis)).replace('__EDGE__', edge)
