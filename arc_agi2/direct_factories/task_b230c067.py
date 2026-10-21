"""Direct visible-coordinate factory for b230c067 (execution worker v4).

Scene: three 8-separated sprites on BG.  Two are copies of a template T; the
third is T with one native column deleted (it may fall apart into several
8-components).  Output: the T copies -> palette[1], all other material ->
palette[2].

The emitted program enumerates three readings and keeps those that reproduce
every demonstration exactly:
  pair_template  - the constructor parse: the unique largest repeated mask
                   occurs exactly twice, and all remaining material, taken
                   together, equals that mask with one line (column in the
                   native frame, i.e. along DEL_AXIS in visible coordinates)
                   deleted.  Pair -> ONE, rest -> TWO.
  all_repeated   - archived reading: every figure whose mask repeats -> ONE.
  exactly_twice  - every figure whose mask occurs exactly twice -> ONE.
No survivor, a survivor undefined on the query, or survivors disagreeing on the
query all raise; there is no fallback, no first/majority choice.
"""

_BODY = r'''
import numpy as np
from collections import deque

_STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


class Ambiguous(ValueError):
    pass


def _components(g):
    h, w = g.shape
    seen = np.zeros((h, w), dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if g[y, x] == BG or seen[y, x]:
                continue
            seen[y, x] = True
            q = deque([(y, x)])
            cells = []
            while q:
                cy, cx = q.popleft()
                cells.append((cy, cx))
                for dy, dx in _STEPS:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and g[ny, nx] != BG and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            out.append(sorted(cells))
    return out


def _norm(cells):
    y0 = min(p[0] for p in cells)
    x0 = min(p[1] for p in cells)
    return frozenset((y - y0, x - x0) for y, x in cells)


def _scene(g):
    comps = _components(g)
    keys = [_norm(c) for c in comps]
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    return comps, keys, counts


def _paint(g, comps, ones):
    out = g.copy()
    for i, cells in enumerate(comps):
        colour = ONE if i in ones else TWO
        for y, x in cells:
            out[y, x] = colour
    return out


def _delete_line(mask, j):
    out = []
    for y, x in mask:
        c = x if DEL_AXIS == 1 else y
        if c == j:
            continue
        if c > j:
            if DEL_AXIS == 1:
                x -= 1
            else:
                y -= 1
        out.append((y, x))
    return _norm(out) if out else frozenset()


def _rule_pair_template(g):
    comps, keys, counts = _scene(g)
    rep = [k for k in counts if counts[k] > 1]
    if not rep:
        return None
    best = max(len(k) for k in rep)
    top = [k for k in rep if len(k) == best]
    if len(top) != 1 or counts[top[0]] != 2:
        return None
    tk = top[0]
    rest = [p for c, k in zip(comps, keys) if k != tk for p in c]
    if not rest:
        return None
    target = _norm(rest)
    span = max((p[1] if DEL_AXIS == 1 else p[0]) for p in tk) + 1
    if not any(_delete_line(tk, j) == target for j in range(span)):
        return None
    return _paint(g, comps, set(i for i, k in enumerate(keys) if k == tk))


def _rule_all_repeated(g):
    comps, keys, counts = _scene(g)
    if not comps:
        return None
    return _paint(g, comps, set(i for i, k in enumerate(keys) if counts[k] > 1))


def _rule_exactly_twice(g):
    comps, keys, counts = _scene(g)
    if not comps:
        return None
    return _paint(g, comps, set(i for i, k in enumerate(keys) if counts[k] == 2))


_RULES = (('pair_template', _rule_pair_template),
          ('all_repeated', _rule_all_repeated),
          ('exactly_twice', _rule_exactly_twice))


def _pair(d):
    if isinstance(d, dict):
        return d['input'], d['output']
    return d[0], d[1]


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    demos = [_pair(d) for d in demonstrations]
    if not demos:
        raise Ambiguous('no demonstrations')
    alive = []
    for name, rule in _RULES:
        ok = True
        for i, o in demos:
            p = rule(np.array(i, dtype=int))
            e = np.array(o, dtype=int)
            if p is None or p.shape != e.shape or not np.array_equal(p, e):
                ok = False
                break
        if ok:
            alive.append((name, rule))
    if not alive:
        raise Ambiguous('no reading reproduces every demonstration')
    preds = []
    for name, rule in alive:
        p = rule(g)
        if p is None:
            raise Ambiguous('surviving reading %s undefined on query' % name)
        preds.append(p)
    for p in preds[1:]:
        if not np.array_equal(p, preds[0]):
            raise Ambiguous('surviving readings disagree on query: %s'
                            % ','.join(n for n, _ in alive))
    return preds[0].tolist()
'''


def build_program(d4, palette):
    bg = int(palette[0])
    one = int(palette[1])
    two = int(palette[2])
    # transformed(): optional row reversal (keeps columns as columns), then
    # d4 % 4 clockwise rotations; an odd count swaps rows and columns.
    del_axis = 1 if (int(d4) % 4) % 2 == 0 else 0
    header = 'BG = %d\nONE = %d\nTWO = %d\nDEL_AXIS = %d\n' % (bg, one, two, del_axis)
    return header + _BODY
