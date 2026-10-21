"""Demo-evidence gate for bd14c3bf (second-review v6, independent implementation).

Rule family: the template object (template colour) selects every other object
whose *shape* is equivalent to it; selected objects are repainted with the
template colour.  What "equivalent shape" means is the hypothesis.  This gate
fits a finite, documented set of shape-equivalence hypotheses to the
demonstrations, then requires every surviving hypothesis to produce the same
full output on every query input.  It reads demonstration inputs/outputs and
query *inputs* only; a query 'output' key, if present, is never read.

Hypotheses = normal form x orientation group:
  normal forms  exact     cropped mask
                collapse  cropped mask with repeated adjacent rows/cols merged
                lattice   stroke-length-invariant vertex lattice
                family    collapse OR lattice (what the direct program uses)
                topo      (number of holes, number of stroke ends) - coarse
  groups        identity, rotations (C4), all eight rotations/reflections (D4)
The topo form is orientation-free, so it appears once.  13 hypotheses total.

Raises MissingBd14c3bfEvidence when demonstrations fit no hypothesis, when
roles cannot be read from pixels, or when surviving hypotheses disagree on a
query (context shortfall: keep the query, resample demonstrations).
"""
from collections import Counter


class MissingBd14c3bfEvidence(ValueError):
    pass


STEPS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def _objects(g, ink):
    todo = {(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == ink}
    found = []
    while todo:
        seed = min(todo)
        todo.discard(seed)
        part, stack = [seed], [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in STEPS:
                p = (r + dr, c + dc)
                if p in todo:
                    todo.discard(p)
                    part.append(p)
                    stack.append(p)
        found.append(frozenset(part))
    return found


def _mask(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    h = max(r for r, _ in cells) - r0 + 1
    w = max(c for _, c in cells) - c0 + 1
    return tuple(tuple(int((r0 + i, c0 + j) in cells) for j in range(w)) for i in range(h))


def _dedupe(rows):
    kept = []
    for row in rows:
        if not kept or kept[-1] != row:
            kept.append(row)
    return kept


def _collapse(m):
    m = _dedupe(list(m))
    cols = _dedupe(list(zip(*m)))
    return tuple(zip(*cols))


def _lattice(cells):
    """Vertices = cells that are not straight pass-throughs; edges = straight runs."""
    def nbrs(p):
        return [(dr, dc) for dr, dc in STEPS if (p[0] + dr, p[1] + dc) in cells]
    verts = set()
    for p in cells:
        n = nbrs(p)
        if not (len(n) == 2 and n[0][0] == -n[1][0] and n[0][1] == -n[1][1]):
            verts.add(p)
    if not verts:
        return ('cycle-without-vertex',)
    rows = {r: 2 * i for i, r in enumerate(sorted({r for r, _ in verts}))}
    cols = {c: 2 * i for i, c in enumerate(sorted({c for _, c in verts}))}
    lit = set()
    for p in verts:
        a = (rows[p[0]], cols[p[1]])
        lit.add(a)
        for dr, dc in nbrs(p):
            q = (p[0] + dr, p[1] + dc)
            while q not in verts:
                q = (q[0] + dr, q[1] + dc)
                if q not in cells:
                    return ('unwalkable',)
            b = (rows[q[0]], cols[q[1]])
            for i in range(min(a[0], b[0]), max(a[0], b[0]) + 1):
                for j in range(min(a[1], b[1]), max(a[1], b[1]) + 1):
                    lit.add((i, j))
    return _mask(frozenset(lit))


def _topo(cells):
    r0 = min(r for r, _ in cells) - 1
    r1 = max(r for r, _ in cells) + 1
    c0 = min(c for _, c in cells) - 1
    c1 = max(c for _, c in cells) + 1
    empty = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)} - set(cells)
    regions = 0
    while empty:
        stack = [empty.pop()]
        regions += 1
        while stack:
            r, c = stack.pop()
            for dr, dc in STEPS:
                p = (r + dr, c + dc)
                if p in empty:
                    empty.discard(p)
                    stack.append(p)
    ends = sum(1 for r, c in cells
               if sum((r + dr, c + dc) in cells for dr, dc in STEPS) == 1)
    return ('topo', regions - 1, ends)


def _rot(m):
    return tuple(zip(*m[::-1]))


def _orbit(m, group):
    out, cur = set(), m
    for _ in range(4 if group != 'id' else 1):
        out.add(cur)
        if group == 'd4':
            out.add(tuple(row[::-1] for row in cur))
        cur = _rot(cur)
    return out


def _forms(cells, form):
    if form == 'exact':
        return [_mask(cells)]
    if form == 'collapse':
        return [_collapse(_mask(cells))]
    if form == 'lattice':
        return [_lattice(cells)]
    if form == 'family':
        return [_collapse(_mask(cells)), _lattice(cells)]
    raise KeyError(form)


HYPOTHESES = [(f, g) for f in ('exact', 'collapse', 'lattice', 'family')
              for g in ('id', 'c4', 'd4')] + [('topo', None)]


def _predict(g, bg, tpl, hyp):
    form, group = hyp
    out = [list(row) for row in g]
    templates = _objects(g, tpl)
    if not templates:
        raise MissingBd14c3bfEvidence('bd14c3bf: no template-coloured object')
    inks = sorted({v for row in g for v in row} - {bg, tpl})
    if form == 'topo':
        keys = {_topo(t) for t in templates}
        match = lambda cells: _topo(cells) in keys
    else:
        keys = [set() for _ in _forms(templates[0], form)]
        for t in templates:
            for i, f in enumerate(_forms(t, form)):
                if not (isinstance(f, tuple) and f and isinstance(f[0], str)):
                    keys[i] |= _orbit(f, group)
        match = lambda cells: any(f in keys[i] for i, f in enumerate(_forms(cells, form)))
    for ink in inks:
        for cells in _objects(g, ink):
            if match(cells):
                for r, c in cells:
                    out[r][c] = tpl
    return out


def _roles(demonstrations, queries, palette):
    if palette is not None:
        return int(palette[0]), int(palette[2])
    painted = Counter()
    for d in demonstrations:
        for ra, rb in zip(d['input'], d['output']):
            for a, b in zip(ra, rb):
                if a != b:
                    painted[b] += 1
    if len(painted) != 1:
        raise MissingBd14c3bfEvidence('bd14c3bf: template colour not shown by demonstrations')
    tpl = next(iter(painted))
    seen = Counter(v for x in list(demonstrations) + list(queries) for row in x['input'] for v in row)
    ranked = seen.most_common(2)
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise MissingBd14c3bfEvidence('bd14c3bf: background colour tie')
    return ranked[0][0], tpl


def require_bd14c3bf_evidence(demonstrations, queries, palette=None, d4=None):
    """Return survivor report or raise MissingBd14c3bfEvidence.  d4 is unused:
    the hypothesis set is closed under all rotations/reflections."""
    if not demonstrations:
        raise MissingBd14c3bfEvidence('bd14c3bf: no demonstrations')
    bg, tpl = _roles(demonstrations, queries, palette)
    alive = []
    for hyp in HYPOTHESES:
        try:
            if all(_predict(d['input'], bg, tpl, hyp) == [list(r) for r in d['output']]
                   for d in demonstrations):
                alive.append(hyp)
        except MissingBd14c3bfEvidence:
            continue
    if not alive:
        raise MissingBd14c3bfEvidence('bd14c3bf: demonstrations fit no shape hypothesis')
    for k, q in enumerate(queries):
        outs = {}
        for hyp in alive:
            key = tuple(map(tuple, _predict(q['input'], bg, tpl, hyp)))
            outs.setdefault(key, []).append(hyp)
        if len(outs) > 1:
            raise MissingBd14c3bfEvidence(
                'bd14c3bf: demonstrations leave query %d ambiguous between %s'
                % (k, sorted(sorted(v) for v in outs.values())))
    return {'background': bg, 'template_colour': tpl,
            'surviving_hypotheses': [list(h) for h in alive]}
