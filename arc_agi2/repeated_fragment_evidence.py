"""Independent episode-evidence gate for b230c067 (does not import factory.py).

Never receives query answers.  Implementation differs from the emitted
program: union-find 8-components, tuple-sorted shape keys, and an exhaustive
enumeration of ALL constructor parses (any equal-mask pair, any deleted line),
not the 'largest repeated mask' shortcut.

Statuses:
  determined           every reading consistent with the demos gives the same
                       query output, and the constructor parse is unique
  context_shortfall    query parse is unique (intrinsically identifiable) but
                       readings the demos do not refute disagree on it ->
                       keep the query, resample demonstrations
  intrinsic_ambiguity  the visible query admits >1 constructor parse with
                       different labels -> no demos can fix it, reject query
  not_constructor      no constructor parse of the query
"""
from collections import defaultdict


def _cells(g, bg):
    return [(y, x) for y, row in enumerate(g) for x, v in enumerate(row) if v != bg]


def components(g, bg):
    cells = _cells(g, bg)
    parent = {c: c for c in cells}

    def find(c):
        while parent[c] != c:
            parent[c] = parent[parent[c]]
            c = parent[c]
        return c

    for (y, x) in cells:
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                n = (y + dy, x + dx)
                if n in parent:
                    a, b = find((y, x)), find(n)
                    if a != b:
                        parent[a] = b
    groups = defaultdict(list)
    for c in cells:
        groups[find(c)].append(c)
    return sorted((sorted(v) for v in groups.values()), key=lambda v: v[0])


def shape(cells):
    y0 = min(y for y, _ in cells)
    x0 = min(x for _, x in cells)
    return tuple(sorted((y - y0, x - x0) for y, x in cells))


def minus_line(sh, axis, j):
    kept = []
    for p in sh:
        if p[axis] == j:
            continue
        q = list(p)
        if p[axis] > j:
            q[axis] -= 1
        kept.append(tuple(q))
    return shape(kept) if kept else ()


def constructor_parses(comps, axis):
    """All labelings (frozenset of ONE-component indices) explained by
    'two copies of T + (T minus one line along axis), possibly split'."""
    keys = [shape(c) for c in comps]
    out = set()
    n = len(comps)
    for a in range(n):
        for b in range(a + 1, n):
            if keys[a] != keys[b]:
                continue
            rest = [p for i, c in enumerate(comps) if i not in (a, b) for p in c]
            if not rest:
                continue
            target = shape(rest)
            span = max(p[axis] for p in keys[a]) + 1
            if any(minus_line(keys[a], axis, j) == target for j in range(span)):
                out.add(frozenset((a, b)))
    return out


def readings(comps, axis):
    keys = [shape(c) for c in comps]
    cnt = defaultdict(int)
    for k in keys:
        cnt[k] += 1
    parses = constructor_parses(comps, axis)
    r = {
        'all_repeated': frozenset(i for i, k in enumerate(keys) if cnt[k] > 1),
        'exactly_twice': frozenset(i for i, k in enumerate(keys) if cnt[k] == 2),
        'constructor': next(iter(parses)) if len(parses) == 1 else None,
    }
    return r, parses


def paint(g, comps, ones, one, two):
    out = [list(r) for r in g]
    for i, c in enumerate(comps):
        for y, x in c:
            out[y][x] = one if i in ones else two
    return out


def axis_for(d4):
    # native column index lives on axis 1 unless an odd number of rotations
    return 1 if (d4 % 4) % 2 == 0 else 0


def gate(train, query_input, palette, d4):
    bg, one, two = palette[0], palette[1], palette[2]
    axis = axis_for(d4)
    alive = {'constructor', 'all_repeated', 'exactly_twice'}
    for d in train:
        comps = components(d['input'], bg)
        r, _ = readings(comps, axis)
        for name in list(alive):
            ones = r[name]
            if ones is None or paint(d['input'], comps, ones, one, two) != d['output']:
                alive.discard(name)
    qc = components(query_input, bg)
    r, parses = readings(qc, axis)
    info = {'alive': sorted(alive), 'query_components': len(qc),
            'query_parses': len(parses),
            'query_readings_disagree': len({r[k] for k in r if r[k] is not None}) > 1}
    if len(parses) == 0:
        return 'not_constructor', info
    if len(parses) > 1:
        return 'intrinsic_ambiguity', info
    if not alive:
        return 'demos_unexplained', info
    labels = {r[k] for k in alive}
    if len(labels) == 1:
        return 'determined', info
    return 'context_shortfall', info


def require_fragment_evidence(demonstrations, queries, palette, d4=0):
    from .colour_evidence import MissingColourEvidence
    for query in queries:
        status,info=gate(demonstrations,query['input'],palette,d4)
        if status!='determined':raise MissingColourEvidence('b230c067: '+status)
