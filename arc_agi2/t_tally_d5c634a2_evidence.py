"""Visible demonstration-evidence gate for d5c634a2 (T-tetromino tallies).

The gate reads only visible grids: demonstration inputs and outputs, and
query INPUTS. It takes no D4 index and no palette, and it is never told
which stem direction is "up". Everything is recovered from the grids as
they appear, so the gate is the same for raw and augmented episodes.
Pass queries as [{'input': grid}]. Any query 'output' key is ignored.

Hypothesis class (deliberately broad):
  * Parse. Foreground cells are covered by T-tetrominoes in any of the
    4 stem directions. Overlaps are allowed, but every T must own a cell
    that no other T covers. If two covers give different direction
    tallies, the grid is intrinsically ambiguous and the gate rejects it.
  * Rule. Some map sigma sends each of the 4 visible stem directions
    either to one output tally colour or to "ignored". For each colour X,
    an ARBITRARY nested chain of cell sets S_X(n) with |S_X(n)| = n gives
    the marks drawn when n objects map to X. The output canvas has a
    fixed shape and the demonstration background colour.
A rule is consistent when it reproduces every demonstration output
exactly. The query passes only when every consistent rule predicts the
same full output grid. That requires two things:
  * The colour/orientation association must be pinned, or it must not
    matter for this query.
  * Every non-zero query tally n must have S_X(n) observed in some demo.
    The demos never pin an unobserved prefix: at least two completions
    always remain.
"""
from itertools import product

try:
    from .colour_evidence import MissingColourEvidence
except ImportError:  # standalone use with the fork on sys.path
    from arc_agi2.colour_evidence import MissingColourEvidence

DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
MAX_COVER_NODES = 200000


class MissingTTallyEvidence(MissingColourEvidence):
    """reason is a short code. intrinsic=True means that no demonstrations
    could help, because the query input itself is ambiguous or outside the
    rule class. intrinsic=False is a context shortfall: resample demos and
    keep the query."""

    def __init__(self, reason, intrinsic=False):
        super().__init__('d5c634a2: ' + reason)
        self.reason = reason
        self.intrinsic = intrinsic


def _colours(g):
    return {v for row in g for v in row}


def _majority(g):
    counts = {}
    for row in g:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    best = max(counts.values())
    top = [k for k, n in counts.items() if n == best]
    total = sum(counts.values())
    if len(top) != 1 or 2 * best <= total:
        return None
    return top[0]


def t_placements(fg):
    """All T-tetrominoes (centre, stem direction) whose 4 cells are in fg."""
    out = []
    for (r, c) in sorted(fg):
        for d in DIRECTIONS:
            pr, pc = d[1], d[0]  # perpendicular to the stem = bar axis
            cells = frozenset({(r, c), (r + pr, c + pc), (r - pr, c - pc), (r + d[0], c + d[1])})
            if cells <= fg:
                out.append((cells, d))
    return out


def cover_tallies(g, background):
    """Set of direction tallies over every irredundant T cover of the
    non-background cells. Each tally is a tuple of counts, ordered like
    DIRECTIONS."""
    h, w = len(g), len(g[0])
    fg = frozenset((r, c) for r in range(h) for c in range(w) if g[r][c] != background)
    if not fg:
        return set()
    places = t_placements(fg)
    by_cell = {x: [i for i, (cells, _) in enumerate(places) if x in cells] for x in fg}
    if any(not v for v in by_cell.values()):
        return set()
    covers = set()
    nodes = [0]

    def rec(chosen, covered):
        nodes[0] += 1
        if nodes[0] > MAX_COVER_NODES:
            raise MissingTTallyEvidence('cover_search_limit', intrinsic=True)
        if covered == fg:
            covers.add(frozenset(chosen))
            return
        x = min(fg - covered)
        for i in by_cell[x]:
            if i not in chosen:
                rec(chosen | {i}, covered | places[i][0])

    rec(frozenset(), frozenset())
    tallies = set()
    for cov in covers:
        ok = True
        for i in cov:
            others = set().union(*[places[j][0] for j in cov if j != i]) if len(cov) > 1 else set()
            if places[i][0] <= others:
                ok = False
                break
        if ok:
            tallies.add(tuple(sum(1 for i in cov if places[i][1] == d) for d in DIRECTIONS))
    return tallies


def _unique_tally(g, background, foreground, role):
    cols = _colours(g)
    if not cols <= {background, foreground} or foreground not in cols:
        raise MissingTTallyEvidence(role + '_colours_outside_demo_context', intrinsic=(role == 'query'))
    t = cover_tallies(g, background)
    if len(t) != 1:
        raise MissingTTallyEvidence(role + ('_no_t_cover' if not t else '_t_cover_ambiguous'),
                                    intrinsic=(role == 'query'))
    return next(iter(t))


def fit_rules(demonstrations):
    """Return (background, foreground, out_shape, colours, rules) where every
    rule is (sigma, observed). sigma maps direction index -> colour or None.
    observed[X][n] is the cell set that shows n tallies of colour X."""
    if not demonstrations:
        raise MissingTTallyEvidence('no_demonstrations')
    bgs = {_majority(d['output']) for d in demonstrations}
    if len(bgs) != 1 or None in bgs:
        raise MissingTTallyEvidence('output_background_unobserved')
    bg = bgs.pop()
    fgs = set()
    for d in demonstrations:
        cols = _colours(d['input'])
        if bg not in cols or len(cols) != 2:
            raise MissingTTallyEvidence('demo_input_not_two_colour')
        fgs |= cols - {bg}
    if len(fgs) != 1:
        raise MissingTTallyEvidence('object_colour_inconsistent')
    fg = fgs.pop()
    shapes = {(len(d['output']), len(d['output'][0])) for d in demonstrations}
    if len(shapes) != 1:
        raise MissingTTallyEvidence('output_shape_inconsistent')
    shape = shapes.pop()
    colours = sorted(set().union(*[_colours(d['output']) for d in demonstrations]) - {bg})
    if len(colours) > 4:
        raise MissingTTallyEvidence('too_many_tally_colours')
    tallies = [_unique_tally(d['input'], bg, fg, 'demo') for d in demonstrations]
    marks = []
    for d in demonstrations:
        m = {X: frozenset() for X in colours}
        for r, row in enumerate(d['output']):
            for c, v in enumerate(row):
                if v != bg:
                    m[v] = m[v] | {(r, c)}
        marks.append(m)
    rules = []
    for sigma in product([None] + colours, repeat=len(DIRECTIONS)):
        observed = {X: {} for X in colours}
        ok = True
        for t, m in zip(tallies, marks):
            for X in colours:
                n = sum(k for k, s in zip(t, sigma) if s == X)
                cells = m[X]
                if len(cells) != n or observed[X].get(n, cells) != cells:
                    ok = False
                    break
                observed[X][n] = cells
            if not ok:
                break
        if ok:
            for X in colours:  # the chain must be nested
                seq = [observed[X][n] for n in sorted(observed[X])]
                if any(not a <= b for a, b in zip(seq, seq[1:])):
                    ok = False
        if ok:
            rules.append((sigma, observed))
    if not rules:
        raise MissingTTallyEvidence('demonstrations_fit_no_tally_rule')
    return bg, fg, shape, colours, rules


def predict(demonstrations, query_input):
    """Unique output that every consistent rule predicts, or raise."""
    bg, fg, shape, colours, rules = fit_rules(demonstrations)
    t = _unique_tally(query_input, bg, fg, 'query')
    preds = set()
    missing = set()
    for sigma, observed in rules:
        out = [[bg] * shape[1] for _ in range(shape[0])]
        for X in colours:
            n = sum(k for k, s in zip(t, sigma) if s == X)
            if n == 0:
                continue
            if n not in observed[X]:
                missing.add(n)  # this rule alone leaves >= 2 completions
                continue
            for r, c in observed[X][n]:
                out[r][c] = X
        preds.add(tuple(map(tuple, out)))
    if missing:
        raise MissingTTallyEvidence('tally_prefix_%s_unobserved' % '_'.join(map(str, sorted(missing))))
    if len(preds) != 1:
        raise MissingTTallyEvidence('orientation_colour_association_unobserved')
    return [list(row) for row in preds.pop()]


def require_t_tally_evidence(demonstrations, queries, palette=None, d4=None):
    """Dispatch entry. palette and d4 are accepted for signature
    compatibility and deliberately ignored."""
    for q in queries:
        predict(demonstrations, q['input'])
