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
* e0fb7511 (target colour palette[0], mark palette[8]): a target cell is
  marked when it has a 4-adjacent target cell, or (competitor) an 8-adjacent
  one. Demonstrations whose target cells never touch only diagonally cannot
  separate them.
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
ADJACENCIES = ('four', 'eight')              # index 0 is the native rule
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


def adjacency_variants(grid, palette):
    a = _rows(ADJACENCY_TASK, grid)
    target, mark = palette[0], palette[8]
    h, w = len(a), len(a[0])

    def marked(y, x, steps):
        return any(0 <= y + dy < h and 0 <= x + dx < w and a[y + dy][x + dx] == target
                   for dy, dx in steps)
    return [[[mark if v == target and marked(y, x, steps) else v for x, v in enumerate(r)]
             for y, r in enumerate(a)] for steps in (ORTHOGONAL, ORTHOGONAL + DIAGONAL)]


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
    if task_id == ANCHOR_TASK:
        return anchor_variants
    if task_id == ADJACENCY_TASK:
        return lambda g: adjacency_variants(g, palette)
    if task_id == DILATION_TASK:
        return lambda g: dilation_variants(g, palette)
    raise KeyError(task_id)


def surviving_rules(task_id, demonstrations, palette=None):
    """Indices of the candidate rules reproducing every demonstration."""
    palette = list(range(10)) if palette is None else list(palette)
    variants = variants_for(task_id, palette)
    alive = None
    for demo in demonstrations:
        fit = {i for i, out in enumerate(variants(demo['input'])) if out == demo['output']}
        alive = fit if alive is None else alive & fit
    return set() if alive is None else alive


def require_mirror_neighbourhood_evidence(task_id, demonstrations, queries, palette=None):
    """Raise MissingColourEvidence unless every surviving rule agrees per query."""
    from .colour_evidence import _require_rule_agreement
    palette = list(range(10)) if palette is None else list(palette)
    _require_rule_agreement(task_id, demonstrations, queries, variants_for(task_id, palette))
