"""Episode evidence for 4cd1b7b2 (Latin-square hole filling), native batch G.

The gate enumerates a small, explicitly named set of hole-filling rules, keeps
the rules that reproduce EVERY demonstration output, and requires all
survivors to give the same answer on each query INPUT. Query answers are never
read. Passing only rules out the listed alternatives. It is not a claim that
the intended rule is identifiable among all possible rules.

Native rule: a row or column with exactly one hole gets the one colour it is
missing, repeated until nothing changes (``lines-iterated``). Every native
scene is carved one blank at a time from complete lines, so this always
finishes and the completion is the unique Latin square.

Competitors (all sound deductions, but weaker or one-directional):
* ``cells-iterated``: a hole whose row and column leave one candidate colour
  gets it (the archived solver's propagation); identical to the native rule
  on every native scene, kept so that off-domain disagreement is visible.
* ``rows-iterated`` / ``cols-iterated``: only rows (columns) are used.
* ``lines-single-pass``, ``rows-single-pass``, ``cols-single-pass``,
  ``cells-single-pass``: one simultaneous pass on the input; holes that need
  an earlier fill stay holes.
Demonstrations that each need only one pass, or only rows, cannot separate
these from the native rule; a query that needs more is then rejected and the
context is resampled. The set is D4-closed (rows <-> columns), so no episode
metadata is used beyond the hole colour palette[0].

Not gated, with reason (see the batch-G report for counts and witnesses):
a 2x2-box (Sudoku) constraint. Box-valid squares are a subset of Latin
squares, and the native completion is unique, so the box rule either gives
the same answer or has NO completion on the query input. In the second case
the query input itself refutes it. It never predicts a different grid.

The fill colours are taken from the demonstrations (every colour other than
the hole colour shown in them), never from the query answer. If fewer than
four are shown, or the query uses an unseen colour, the context is rejected.
"""

TASK_ID = '4cd1b7b2'
RULES = ('lines-iterated', 'cells-iterated', 'rows-iterated', 'cols-iterated',
         'lines-single-pass', 'rows-single-pass', 'cols-single-pass',
         'cells-single-pass')
NATIVE_RULE = RULES[0]


def _missing(task_id):
    from .colour_evidence import MissingColourEvidence
    return lambda message: MissingColourEvidence(f'{task_id}: {message}')


def _grid(g):
    rows = [list(map(int, r)) for r in g]
    if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
        raise _missing(TASK_ID)('malformed grid')
    return rows


def _fill(g, hole, colours, rule):
    g = _grid(g)
    h, w = len(g), len(g[0])
    kind, mode = rule.split('-', 1)
    row_lines = [[(y, x) for x in range(w)] for y in range(h)]
    col_lines = [[(y, x) for y in range(h)] for x in range(w)]
    lines = {'lines': row_lines + col_lines, 'rows': row_lines,
             'cols': col_lines, 'cells': None}[kind]
    while True:
        fills = {}
        if lines is None:
            for y in range(h):
                for x in range(w):
                    if g[y][x] == hole:
                        left = colours - set(g[y]) - {g[r][x] for r in range(h)}
                        if len(left) == 1:
                            fills[(y, x)] = next(iter(left))
        else:
            for line in lines:
                holes = [p for p in line if g[p[0]][p[1]] == hole]
                left = colours - {g[y][x] for y, x in line}
                if len(holes) == 1 and len(left) == 1:
                    fills.setdefault(holes[0], set()).add(next(iter(left)))
            # A cell forced to two different colours by its row and column
            # is a contradiction; leave it unfilled for this rule.
            fills = {p: next(iter(v)) for p, v in fills.items() if len(v) == 1}
        for (y, x), v in fills.items():
            g[y][x] = v
        if not fills or mode == 'single-pass':
            return tuple(tuple(r) for r in g)


def demonstrated_colours(demonstrations, hole):
    """Every non-hole colour shown in the demonstration inputs or outputs."""
    return {v for d in demonstrations for key in ('input', 'output')
            for row in d[key] for v in row if v != hole}


def variants(g, hole, colours):
    return [_fill(g, hole, colours, rule) for rule in RULES]


def surviving_rules(demonstrations, palette=None):
    palette = list(range(10)) if palette is None else list(palette)
    hole = palette[0]
    colours = demonstrated_colours(demonstrations, hole)
    alive = set(range(len(RULES)))
    for demo in demonstrations:
        target = tuple(tuple(int(v) for v in r) for r in demo['output'])
        alive &= {i for i, out in enumerate(variants(demo['input'], hole, colours))
                  if out == target}
    return alive


def candidate_predictions(demonstrations, query_input, palette=None):
    """Distinct query answers of the rules fitting every demonstration."""
    palette = list(range(10)) if palette is None else list(palette)
    hole = palette[0]
    colours = demonstrated_colours(demonstrations, hole)
    options = variants(query_input, hole, colours)
    answers = []
    for i in sorted(surviving_rules(demonstrations, palette)):
        if options[i] not in answers:
            answers.append(options[i])
    return answers


def require_latin_fill_evidence(demonstrations, queries, palette=None):
    """Raise MissingColourEvidence unless every surviving rule agrees per query."""
    missing = _missing(TASK_ID)
    palette = list(range(10)) if palette is None else list(palette)
    hole = palette[0]
    colours = demonstrated_colours(demonstrations, hole)
    if len(colours) != 4:
        raise missing(f'demonstrations show {len(colours)} fill colours, not 4')
    if not surviving_rules(demonstrations, palette):
        raise missing('demonstrations fit no candidate rule')
    for query in queries:
        if {v for row in query['input'] for v in row} - colours - {hole}:
            raise missing('query uses a colour absent from the demonstrations')
        if len(candidate_predictions(demonstrations, query['input'], palette)) > 1:
            raise missing('demonstrations leave query rule ambiguous')
