"""Episode evidence for d47aa2ff (moved dots between two panels), native batch c7d4/d47a.

Native rule: the input is two equal panels split by a full grey line. The
output is the source panel; a cell that holds a dot in the source panel but
not in the other becomes red (vacated), and a cell empty in the source but
filled in the other becomes blue (arrived).

The gate enumerates a finite, named set of readings, keeps those that
reproduce EVERY demonstration output, and requires every survivor to give the
same answer on each query INPUT. Query answers are never read. A pass rules
out only the listed alternatives; it is not an identifiability proof.

Rules (15), evaluated in the native frame (source panel left, identity
palette) after undoing the episode's D4 transform and colour permutation.
This uses only episode metadata, never an answer:

* ``pixel_diff`` (native);
* ``swapped_markers``, ``markers_only`` (kept dots erased),
  ``arrival_keeps_colour``, ``vacated_only``, ``arrived_only``: each differs
  from the native answer on EVERY valid scene (every scene has a mover and a
  kept dot), so any one demonstration refutes it;
* ``right_panel_base``, ``colour_diff``, ``matched_pairs_only`` (mark a move
  only when exactly one dot of that colour vanished and one appeared): equal
  to the native answer on every valid scene, because the constructor keeps
  one mover per colour and no collisions. Listed so that a broken invariant
  shows up as ambiguity rather than passing silently;
* movement trails ``trail-{line,rows-first,cols-first}-{red,blue}``: the
  native markers plus the path from each dot's old cell to its new cell,
  painted red or blue. ``line`` walks straight or diagonally (a knight-type
  move has no such path: undefined); ``rows-first``/``cols-first`` walk an L.
  A path cell that is not empty in both panels makes the rule undefined.
  These readings agree with the native rule whenever every move is to a
  neighbouring cell, so demonstrations showing only one-step moves cannot
  refute them, while a query with a two-cell move separates them. This is
  the ambiguity the gate exists for; it predates the domain expansion.

The set is closed under D4 (transposition swaps rows-first and cols-first;
line and the static rules are D4-invariant), so the verdict does not depend
on the episode orientation. A survivor that is undefined on the query counts
as a distinct answer.

Not gated, with reason (see the batch report for counts): a learned
colour-to-marker lookup (marker colour depends on the dot colour). Markers
are the same two rule colours in every demonstration and the factory treats
them as palette constants; there is no demonstrated variation for a lookup
to explain.
"""

from .augmentation import transformed

TASK_ID = 'd47aa2ff'
BG, GREY, VACATED, ARRIVED = 0, 5, 2, 1
TRAILS = tuple(f'trail-{path}-{ink}' for path in ('line', 'rows-first', 'cols-first')
               for ink in ('red', 'blue'))
RULES = ('pixel_diff', 'swapped_markers', 'markers_only', 'arrival_keeps_colour',
         'vacated_only', 'arrived_only', 'right_panel_base', 'colour_diff',
         'matched_pairs_only') + TRAILS
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


def panels(g):
    """(left, right) native panels, or None if the grey divider is not central."""
    if not g or not g[0] or len(g[0]) % 2 == 0:
        return None
    w = (len(g[0]) - 1) // 2
    if any(row[w] != GREY for row in g):
        return None
    return [list(row[:w]) for row in g], [list(row[w + 1:]) for row in g]


def _t(g):
    return tuple(tuple(int(v) for v in row) for row in g)


def _diff(left, right, vac, arr, base='left', keep=True):
    out = [list(row) for row in (left if base == 'left' else right)]
    for r, row in enumerate(left):
        for c, a in enumerate(row):
            b = right[r][c]
            if not keep and a == b:
                out[r][c] = BG
            if a != BG and b == BG and vac is not None:
                out[r][c] = vac
            elif a == BG and b != BG and arr is not None:
                out[r][c] = b if arr == 'colour' else arr
    return out


def _changes(left, right):
    gone, came = {}, {}
    for r, row in enumerate(left):
        for c, a in enumerate(row):
            b = right[r][c]
            if a != BG and b == BG:
                gone.setdefault(a, []).append((r, c))
            elif a == BG and b != BG:
                came.setdefault(b, []).append((r, c))
    return gone, came


def _path(start, end, kind):
    """Interior cells of the walk from start to end, or None if undefined."""
    (r0, c0), (r1, c1) = start, end
    dr, dc = r1 - r0, c1 - c0
    sr, sc = (dr > 0) - (dr < 0), (dc > 0) - (dc < 0)
    if kind == 'line':
        if dr and dc and abs(dr) != abs(dc):
            return None
        n = max(abs(dr), abs(dc))
        return [(r0 + t * sr, c0 + t * sc) for t in range(1, n)]
    if kind == 'rows-first':
        walk = [(r0 + t * sr, c0) for t in range(1, abs(dr) + 1)]
        walk += [(r1, c0 + t * sc) for t in range(1, abs(dc) + 1)]
    else:
        walk = [(r0, c0 + t * sc) for t in range(1, abs(dc) + 1)]
        walk += [(r0 + t * sr, c1) for t in range(1, abs(dr) + 1)]
    return walk[:-1]


def _trail(left, right, kind, ink):
    gone, came = _changes(left, right)
    if set(gone) != set(came) or any(len(gone[k]) != 1 or len(came[k]) != 1 for k in gone):
        return None
    out = _diff(left, right, VACATED, ARRIVED)
    for colour in gone:
        cells = _path(gone[colour][0], came[colour][0], kind)
        if cells is None:
            return None
        for r, c in cells:
            if left[r][c] != BG or right[r][c] != BG:
                return None
            out[r][c] = VACATED if ink == 'red' else ARRIVED
    return out


def _colour_diff(left, right):
    out = [list(row) for row in left]
    for r, row in enumerate(left):
        for c, a in enumerate(row):
            if a != right[r][c]:
                out[r][c] = VACATED if right[r][c] == BG else ARRIVED
    return out


def _matched(left, right):
    gone, came = _changes(left, right)
    out = [list(row) for row in left]
    for colour in gone:
        if len(gone[colour]) == 1 and len(came.get(colour, ())) == 1:
            (r0, c0), (r1, c1) = gone[colour][0], came[colour][0]
            out[r0][c0], out[r1][c1] = VACATED, ARRIVED
    return out


def variants(g):
    """Answers of every rule on one native-frame input (None = undefined)."""
    p = panels(g)
    if p is None:
        raise _missing('input lacks two equal panels split by a central grey line')
    left, right = p
    out = {
        'pixel_diff': _diff(left, right, VACATED, ARRIVED),
        'swapped_markers': _diff(left, right, ARRIVED, VACATED),
        'markers_only': _diff(left, right, VACATED, ARRIVED, keep=False),
        'arrival_keeps_colour': _diff(left, right, VACATED, 'colour'),
        'vacated_only': _diff(left, right, VACATED, None),
        'arrived_only': _diff(left, right, None, ARRIVED),
        'right_panel_base': _diff(left, right, VACATED, ARRIVED, base='right'),
        'colour_diff': _colour_diff(left, right),
        'matched_pairs_only': _matched(left, right),
    }
    for name in TRAILS:
        path, ink = name[len('trail-'):].rsplit('-', 1)
        out[name] = _trail(left, right, path, ink)
    return {k: (None if v is None else _t(v)) for k, v in out.items()}


def surviving_rules(demonstrations, palette=None, d4=0):
    palette = list(range(10)) if palette is None else list(palette)
    alive = set(RULES)
    for demo in demonstrations:
        target = _t(native_frame(demo['output'], palette, d4))
        options = variants(native_frame(demo['input'], palette, d4))
        alive = {name for name in alive if options[name] == target}
    return alive


def candidate_predictions(demonstrations, query_input, palette=None, d4=0):
    """Distinct native-frame query answers (None = undefined) of the survivors."""
    palette = list(range(10)) if palette is None else list(palette)
    options = variants(native_frame(query_input, palette, d4))
    answers = []
    for name in sorted(surviving_rules(demonstrations, palette, d4)):
        if options[name] not in answers:
            answers.append(options[name])
    return answers


def require_dot_motion_evidence(demonstrations, queries, palette=None, d4=0):
    """Raise MissingColourEvidence unless all surviving rules agree per query input."""
    palette = list(range(10)) if palette is None else list(palette)
    alive = surviving_rules(demonstrations, palette, d4)
    if not alive:
        raise _missing('demonstrations fit no candidate rule')
    for query in queries:
        options = variants(native_frame(query['input'], palette, d4))
        answers = {options[name] for name in alive}
        if len(answers) != 1 or None in answers:
            raise _missing('demonstrations leave the query reading ambiguous')
