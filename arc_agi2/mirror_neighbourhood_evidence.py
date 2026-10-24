"""Episode evidence for three native batch E families (root-authorised, narrow).

Each gate enumerates a small, explicitly named set of competing rules, keeps
the rules that reproduce EVERY demonstration output, and requires all
survivors to give the same answer on each query INPUT. Query answers are
never read. This only rules out the listed alternatives; it is not a claim
that the intended rule is identifiable among all possible rules.

* 0c786b71 (four-way mirror tiling): the output is 2H x 2W and symmetric
  about both midlines, so it is determined by which mirror image of the
  input fills the top-left quadrant. The four candidates put the unflipped
  input in the TL, TR, BL or BR quadrant. D4 maps this set onto itself, so
  the candidates need no episode metadata. Demonstrations that are all
  left-right (or top-bottom) symmetric cannot separate the anchors that
  differ by that flip, so an asymmetric query is rejected.
* e0fb7511 (target colour palette[0], mark palette[8]): candidates are
  (connectivity, T) for 4- or 8-connected target components and every
  positive integer threshold T; a target cell is marked iff its component
  has at least T cells (native: 4-connected, T = 2; T = 1 marks every target
  cell; T above the largest component marks none). Every demonstration
  output bounds T per connectivity: a marked component of size s gives
  T <= s, an unmarked one T > s, so the survivors form one interval per
  connectivity. Predictions are monotone in T, so the query is checked at
  the two extremal surviving thresholds only. Demonstrations with no
  diagonal-only contact leave 8-connectivity alive; demonstrations without
  an isolated target cell leave T = 1; demonstrations without a marked
  2-cell component leave T >= 3.
* f0df5ff0 (seed palette[1] on background palette[0]): background cells in
  the seed's 3x3 square, or (competitor) its plus-shaped cross, take the
  seed colour. Demonstrations whose seeds have no background diagonal
  neighbour cannot separate them.

Neighbourhoods and the mirror set are D4-invariant, so everything runs in
visible coordinates with the episode palette.
"""

ANCHOR_TASK = '0c786b71'
ADJACENCY_TASK = 'e0fb7511'
DILATION_TASK = 'f0df5ff0'
TASK_IDS = (ANCHOR_TASK, ADJACENCY_TASK, DILATION_TASK)

ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAL = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ANCHORS = ('TL', 'TR', 'BL', 'BR')          # quadrant holding the unflipped input
CONNECTIVITY = {'four': ORTHOGONAL, 'eight': ORTHOGONAL + DIAGONAL}
NATIVE_ADJACENCY = ('four', 2)               # 4-connected components of size >= 2
DILATIONS = ('square', 'cross')              # index 0 is the native rule


def _rows(task_id, grid):
    rows = [list(r) for r in grid]
    if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
        from .colour_evidence import MissingColourEvidence
        raise MissingColourEvidence(f'{task_id}: malformed input grid')
    return rows


def _kaleidoscope(top_left):
    top = [r + r[::-1] for r in top_left]
    return top + top[::-1]


def anchor_variants(grid):
    """Outputs with the unflipped input in the TL, TR, BL, BR quadrant."""
    a = _rows(ANCHOR_TASK, grid)
    flips = (a, [r[::-1] for r in a], a[::-1], [r[::-1] for r in a[::-1]])
    return [_kaleidoscope([list(r) for r in f]) for f in flips]


def _components(rows, colour, steps):
    """Components of `colour` cells under the given neighbour steps."""
    h, w = len(rows), len(rows[0])
    seen, comps = set(), []
    for y in range(h):
        for x in range(w):
            if rows[y][x] != colour or (y, x) in seen:
                continue
            seen.add((y, x))
            cells, stack = [], [(y, x)]
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in steps:
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < h and 0 <= nx < w and (ny, nx) not in seen
                            and rows[ny][nx] == colour):
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            comps.append(cells)
    return comps


def threshold_output(grid, palette, connectivity, threshold):
    """Mark target components with at least `threshold` cells."""
    rows = _rows(ADJACENCY_TASK, grid)
    out = [r[:] for r in rows]
    for cells in _components(rows, palette[0], CONNECTIVITY[connectivity]):
        if len(cells) >= threshold:
            for y, x in cells:
                out[y][x] = palette[8]
    return out


def surviving_thresholds(demonstrations, palette=None):
    """{connectivity: (low, high)}: thresholds low <= T <= high reproduce every
    demonstration (high None means unbounded). Missing keys fit no threshold."""
    palette = list(range(10)) if palette is None else list(palette)
    target, mark = palette[0], palette[8]
    alive = {}
    for name, steps in CONNECTIVITY.items():
        low, high, fits = 1, None, True
        for demo in demonstrations:
            rows, out = _rows(ADJACENCY_TASK, demo['input']), demo['output']
            if len(out) != len(rows) or any(len(o) != len(rows[0]) for o in out):
                fits = False
                break
            if any(v != target and out[y][x] != v
                   for y, r in enumerate(rows) for x, v in enumerate(r)):
                fits = False
                break
            for cells in _components(rows, target, steps):
                shown = {out[y][x] for y, x in cells}
                if shown == {mark}:
                    high = len(cells) if high is None else min(high, len(cells))
                elif shown == {target}:
                    low = max(low, len(cells) + 1)
                else:
                    fits = False
                    break
            if not fits:
                break
        if fits and (high is None or low <= high):
            alive[name] = (low, high)
    return alive


def adjacency_predictions(demonstrations, query_input, palette=None):
    """Distinct query answers at the extremal surviving thresholds.

    The marked cells grow monotonically as T decreases, so every surviving
    (connectivity, T) agrees on the query iff this list has exactly one entry
    (which is then the unique answer). Intermediate thresholds are not
    listed, so with several entries the list need not be exhaustive.
    """
    palette = list(range(10)) if palette is None else list(palette)
    rows = _rows(ADJACENCY_TASK, query_input)
    answers = []
    for name, (low, high) in surviving_thresholds(demonstrations, palette).items():
        sizes = [len(c) for c in _components(rows, palette[0], CONNECTIVITY[name])]
        beyond = max(sizes, default=0) + 1          # every T >= beyond marks nothing
        for threshold in {min(low, beyond), beyond if high is None else min(high, beyond)}:
            answer = threshold_output(rows, palette, name, threshold)
            if answer not in answers:
                answers.append(answer)
    return answers


def dilation_variants(grid, palette):
    a = _rows(DILATION_TASK, grid)
    background, seed = palette[0], palette[1]
    h, w = len(a), len(a[0])
    out = []
    for steps in (ORTHOGONAL + DIAGONAL, ORTHOGONAL):
        o = [r[:] for r in a]
        for y in range(h):
            for x in range(w):
                if a[y][x] != seed:
                    continue
                for dy, dx in steps:
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and a[yy][xx] == background:
                        o[yy][xx] = seed
        out.append(o)
    return out


def variants_for(task_id, palette):
    """Enumerated candidates (0c786b71, f0df5ff0); e0fb7511 uses thresholds."""
    if task_id == ANCHOR_TASK:
        return anchor_variants
    if task_id == DILATION_TASK:
        return lambda g: dilation_variants(g, palette)
    raise KeyError(task_id)


def surviving_rules(task_id, demonstrations, palette=None):
    """Indices of the enumerated candidates reproducing every demonstration."""
    palette = list(range(10)) if palette is None else list(palette)
    variants = variants_for(task_id, palette)
    alive = None
    for demo in demonstrations:
        fit = {i for i, out in enumerate(variants(demo['input'])) if out == demo['output']}
        alive = fit if alive is None else alive & fit
    return set() if alive is None else alive


def candidate_predictions(task_id, demonstrations, query_input, palette=None):
    """Distinct query answers of candidates fitting every demonstration.

    Empty if no candidate fits; exactly one entry iff all fitting candidates
    agree. For e0fb7511 only the extremal thresholds are evaluated.
    """
    palette = list(range(10)) if palette is None else list(palette)
    if task_id == ADJACENCY_TASK:
        return adjacency_predictions(demonstrations, query_input, palette)
    options = variants_for(task_id, palette)(query_input)
    answers = []
    for i in sorted(surviving_rules(task_id, demonstrations, palette)):
        if options[i] not in answers:
            answers.append(options[i])
    return answers


def require_mirror_neighbourhood_evidence(task_id, demonstrations, queries, palette=None):
    """Raise MissingColourEvidence unless every surviving rule agrees per query."""
    from .colour_evidence import MissingColourEvidence
    palette = list(range(10)) if palette is None else list(palette)
    fitted = (surviving_thresholds(demonstrations, palette) if task_id == ADJACENCY_TASK
              else surviving_rules(task_id, demonstrations, palette))
    if not fitted:
        raise MissingColourEvidence(f'{task_id}: demonstrations fit no candidate rule')
    for query in queries:
        if len(candidate_predictions(task_id, demonstrations, query['input'], palette)) > 1:
            raise MissingColourEvidence(f'{task_id}: demonstrations leave query rule ambiguous')
