"""Episode evidence for f3cdc58f (colour-count histogram): bar ORDER readings.

Native rule: count each of the four foreground colours and draw a
bottom-aligned bar of that height for each, in the FIXED legend order
1, 2, 3, 4 (columns 0..3; under augmentation the palette images of 1..4 in
the transformed frame). Every colour appears 1..H times, so every
demonstration output shows all four bars and therefore the legend.

The gate keeps those of three NATURAL bar-order readings that reproduce every
demonstration output exactly, and requires every survivor to give the same
answer on each query INPUT. Query answers are never read. This is a bounded
check against the named readings only, not an identifiability proof:

* ``fixed_legend`` (native): bars in the legend order L observed from the
  demonstrations' bars. Any other fixed order is refuted by a single
  demonstration, because every demonstration shows all four bars;
* ``ascending_count``: bars sorted by count, smallest first;
* ``descending_count``: bars sorted by count, largest first.

Count ties are broken by the same observed legend L. In the native frame L is
(1, 2, 3, 4), so the tie-break equals the native colour order used by the
domain review. Reading the tie-break from the bars rather than from visible
colour numbers keeps the readings palette-covariant: the verdict does not
depend on the episode's colour permutation or D4 transform, which are undone
from episode metadata only. (A visible-number tie-break would be a different,
palette-dependent family; it is deliberately not used.)

Demonstrations whose counts are monotone in L fit a count-sorted reading as
well as the fixed legend. The gate is query-specific: such a context is still
accepted when the surviving readings agree on the query, e.g. when the query's
counts are also monotone or all tied. Production retries demonstrations for
the same query (MissingColourEvidence), never a different query.

Not gated (no measured ambiguity in the domain review, 0/2000 contexts at
4x4, 10x10 and default shapes): first-appearance order. Unobserved arbitrary
legends are not enumerated.
"""

from .augmentation import transformed

TASK_ID = 'f3cdc58f'
BG = 0
COLOURS = (1, 2, 3, 4)
RULES = ('fixed_legend', 'ascending_count', 'descending_count')
NATIVE_RULE = RULES[0]


def _missing(message):
    from .colour_evidence import MissingColourEvidence
    return MissingColourEvidence(f'{TASK_ID}: {message}')


def native_frame(g, palette, d4):
    """Undo the episode colour permutation and D4 transform (metadata only)."""
    inverse = {v: k for k, v in enumerate(palette)}
    a = [[inverse[int(c)] for c in row] for row in g]
    a = transformed(a, (-d4) % 4, list(range(10)))
    if d4 >= 4:
        a = [row[::-1] for row in a]
    return a


def counts(g):
    """Native-frame counts of colours 1..4; raises outside the histogram domain."""
    h = len(g)
    if not h or len(g[0]) < 4 or any(len(row) != len(g[0]) for row in g):
        raise _missing('input is not a rectangle at least four columns wide')
    flat = [int(v) for row in g for v in row]
    if any(v not in (BG,) + COLOURS for v in flat):
        raise _missing('input has colours outside the background and four bar colours')
    n = {c: flat.count(c) for c in COLOURS}
    if not all(1 <= n[c] <= h for c in COLOURS):
        raise _missing('input counts are outside 1..height')
    return n


def observed_legend(demonstrations, palette, d4):
    """Common native-frame bar order shown on the bottom row of every demo output."""
    legend = None
    for demo in demonstrations:
        out = native_frame(demo['output'], palette, d4)
        if not out or len(out[0]) < 4:
            raise _missing('demonstration output is narrower than four bars')
        bars = tuple(int(v) for v in out[-1][:4])
        if sorted(bars) != list(COLOURS):
            raise _missing('demonstration output does not show four distinct bars')
        if legend is not None and bars != legend:
            raise _missing('demonstration bars show no common legend')
        legend = bars
    if legend is None:
        raise _missing('no demonstrations')
    return legend


def bar_order(n, rule, legend):
    rank = {c: i for i, c in enumerate(legend)}
    if rule == 'fixed_legend':
        return tuple(legend)
    if rule == 'ascending_count':
        return tuple(sorted(legend, key=lambda c: (n[c], rank[c])))
    if rule == 'descending_count':
        return tuple(sorted(legend, key=lambda c: (-n[c], rank[c])))
    raise KeyError(rule)


def _render(g, n, order):
    h, w = len(g), len(g[0])
    out = [[BG] * w for _ in range(h)]
    for col, colour in enumerate(order):
        for r in range(n[colour]):
            out[h - 1 - r][col] = colour
    return tuple(tuple(row) for row in out)


def variants(g, legend):
    """Native-frame answers of every reading on one native-frame input."""
    n = counts(g)
    return {rule: _render(g, n, bar_order(n, rule, legend)) for rule in RULES}


def _t(g):
    return tuple(tuple(int(v) for v in row) for row in g)


def surviving_rules(demonstrations, palette=None, d4=0):
    palette = list(range(10)) if palette is None else list(palette)
    legend = observed_legend(demonstrations, palette, d4)
    alive = set(RULES)
    for demo in demonstrations:
        target = _t(native_frame(demo['output'], palette, d4))
        options = variants(native_frame(demo['input'], palette, d4), legend)
        alive = {rule for rule in alive if options[rule] == target}
    return alive


def candidate_predictions(demonstrations, query_input, palette=None, d4=0):
    """Distinct VISIBLE-frame query answers of the surviving readings."""
    palette = list(range(10)) if palette is None else list(palette)
    legend = observed_legend(demonstrations, palette, d4)
    options = variants(native_frame(query_input, palette, d4), legend)
    answers = []
    for rule in sorted(surviving_rules(demonstrations, palette, d4)):
        visible = transformed([list(row) for row in options[rule]], d4, palette)
        if visible not in answers:
            answers.append(visible)
    return answers


def require_histogram_order_evidence(demonstrations, queries, palette=None, d4=0):
    """Raise MissingColourEvidence unless the surviving readings agree per query input."""
    palette = list(range(10)) if palette is None else list(palette)
    alive = surviving_rules(demonstrations, palette, d4)
    if NATIVE_RULE not in alive:
        raise _missing('demonstrations do not fit the fixed-legend histogram')
    legend = observed_legend(demonstrations, palette, d4)
    for query in queries:
        options = variants(native_frame(query['input'], palette, d4), legend)
        if len({options[rule] for rule in alive}) != 1:
            raise _missing('demonstrations leave the query bar order ambiguous')
