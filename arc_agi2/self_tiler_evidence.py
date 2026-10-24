"""Demonstration evidence for the three self-tiling families 27f8ce4f, 48f8583b, 5b6cbef5.

All three map an H x W input to an (H*H) x (W*W) canvas of H x W blocks: block
(r, c) holds a copy of the input when input cell (r, c) is selected, and the
fill colour otherwise. They differ only in the selector: the unique modal
colour (27f8ce4f), the unique least frequent colour (48f8583b), or every
non-background cell (5b6cbef5). Many other self-tiling rules fit a few
demonstrations equally well, for example a fixed colour that happens to be the
selected colour in every demo, the opposite frequency extreme, or stamping every
cell. Monochrome demonstrations also never show the fill colour.

This gate keeps every candidate from a FINITE family that reproduces every
demonstration exactly, then requires all survivors to predict the same grid for
each query INPUT. Query answers are never read. If the demonstrations leave the
query ambiguous, MissingColourEvidence asks the caller to resample the
demonstrations for the same query. The gate rules out only the listed
alternatives. It is not an identifiability proof.

Candidate = (selector, placement, content, fill):

* selector: modal | minority | non_modal | non_minority (each undefined on ties),
  all, colour:c and not_colour:c for each visible colour c, and corner:k (cells
  equal to the colour of corner k);
* placement: a D4 transform of the selection mask over the block grid (the four
  shape-preserving ones, plus the four transposing ones for square inputs);
* content: the same D4 transforms of the input tile, or 'solid' (the block is
  filled with the colour of the placed cell that selects it);
* fill: the colour of unselected blocks, any of 0..9, fixed only by
  demonstrations that show an unselected block.

A candidate that is undefined on a demonstration does not fit it. A surviving
candidate that is undefined on the query counts as a distinct prediction
(None), so it also blocks acceptance, and a sole None answer (every survivor
undefined on the query) is a failure, never an accepted answer.
"""
from collections import Counter

from .colour_evidence import MissingColourEvidence

TASK_IDS = ('27f8ce4f', '48f8583b', '5b6cbef5')


def exported_candidate(task_id, palette=None):
    """The exported rule in the candidate vocabulary (used by tests and audits only)."""
    bg = (list(range(10)) if palette is None else list(palette))[0]
    selector = {'27f8ce4f': 'modal', '48f8583b': 'minority',
                '5b6cbef5': f'not_colour:{bg}'}[task_id]
    return selector, 'id', 'id', bg


SHAPE_PRESERVING = ('id', 'flip_h', 'flip_v', 'rot180')
TRANSPOSING = ('transpose', 'anti_transpose', 'rot90', 'rot270')
CORNERS = ('tl', 'tr', 'bl', 'br')
SELECTORS = (('modal', 'minority', 'non_modal', 'non_minority', 'all')
             + tuple(f'colour:{c}' for c in range(10))
             + tuple(f'not_colour:{c}' for c in range(10))
             + tuple(f'corner:{k}' for k in CORNERS))
CONTENTS = SHAPE_PRESERVING + TRANSPOSING + ('solid',)
ALL_FILLS = frozenset(range(10))


def _d4(g, name):
    if name == 'id':
        return [list(r) for r in g]
    if name == 'flip_h':
        return [list(r[::-1]) for r in g]
    if name == 'flip_v':
        return [list(r) for r in g[::-1]]
    if name == 'rot180':
        return [list(r[::-1]) for r in g[::-1]]
    t = [list(r) for r in zip(*g)]
    if name == 'transpose':
        return t
    if name == 'anti_transpose':
        return [list(r[::-1]) for r in t[::-1]]
    if name == 'rot90':          # clockwise
        return [list(r[::-1]) for r in t]
    if name == 'rot270':
        return [list(r) for r in t[::-1]]
    raise ValueError(name)


def placements(h, w):
    return SHAPE_PRESERVING + (TRANSPOSING if h == w else ())


def _selection(g, selector):
    """Boolean H x W mask, or None where the selector is undefined."""
    h, w = len(g), len(g[0])
    cells = [v for r in g for v in r]
    if selector == 'all':
        return [[True] * w for _ in range(h)]
    kind, _, arg = selector.partition(':')
    if kind in ('modal', 'minority', 'non_modal', 'non_minority'):
        counts = Counter(cells).most_common()
        if kind in ('minority', 'non_minority'):
            counts = counts[::-1]
        if len(counts) > 1 and counts[0][1] == counts[1][1]:
            return None
        target, keep = counts[0][0], not kind.startswith('non_')
        return [[(v == target) == keep for v in r] for r in g]
    if kind == 'colour':
        return [[v == int(arg) for v in r] for r in g]
    if kind == 'not_colour':
        return [[v != int(arg) for v in r] for r in g]
    if kind == 'corner':
        target = {'tl': g[0][0], 'tr': g[0][-1], 'bl': g[-1][0], 'br': g[-1][-1]}[arg]
        return [[v == target for v in r] for r in g]
    raise ValueError(selector)


def _blocks(g, out):
    """Split an (H*H) x (W*W) output into H x W blocks, or None on a shape mismatch."""
    h, w = len(g), len(g[0])
    if len(out) != h * h or any(len(r) != w * w for r in out):
        return None
    return [[[list(out[r * h + y][c * w:(c + 1) * w]) for y in range(h)]
             for c in range(w)] for r in range(h)]


class _Pair:
    """Per-grid caches shared by every candidate."""

    def __init__(self, g):
        self.g = [list(r) for r in g]
        self.h, self.w = len(g), len(g[0])
        self.place = placements(self.h, self.w)
        self._sel, self._tile, self._placed = {}, {}, {}

    def selection(self, selector, placement):
        key = (selector, placement)
        if key not in self._sel:
            base = _selection(self.g, selector)
            self._sel[key] = None if base is None else _d4(base, placement)
        return self._sel[key]

    def placed(self, placement):
        if placement not in self._placed:
            self._placed[placement] = _d4(self.g, placement)
        return self._placed[placement]

    def tile(self, content):
        if content not in self._tile:
            self._tile[content] = _d4(self.g, content)
        return self._tile[content]

    def block(self, placement, content, r, c):
        if content == 'solid':
            return [[self.placed(placement)[r][c]] * self.w for _ in range(self.h)]
        return self.tile(content)


def _defined(pair, placement, content):
    return placement in pair.place and (content == 'solid' or content in pair.place)


def _fit(pair, blocks, selector, placement, content):
    """Fills allowed by one demonstration (empty frozenset = does not fit)."""
    if not _defined(pair, placement, content):
        return frozenset()
    mask = pair.selection(selector, placement)
    if mask is None:
        return frozenset()
    fill = None
    for r in range(pair.h):
        for c in range(pair.w):
            b = blocks[r][c]
            if mask[r][c]:
                if b != pair.block(placement, content, r, c):
                    return frozenset()
            else:
                values = {v for row in b for v in row}
                if len(values) != 1:
                    return frozenset()
                (v,) = values
                if fill is None:
                    fill = v
                elif fill != v:
                    return frozenset()
    return ALL_FILLS if fill is None else frozenset((fill,))


def surviving_candidates(demonstrations):
    """{(selector, placement, content): allowed fills} fitting EVERY demonstration."""
    alive = None
    for demo in demonstrations:
        pair = _Pair(demo['input'])
        blocks = _blocks(pair.g, demo['output'])
        if blocks is None:
            return {}
        keys = (alive.keys() if alive is not None else
                [(s, p, c) for s in SELECTORS for p in pair.place for c in CONTENTS])
        nxt = {}
        for key in keys:
            fills = _fit(pair, blocks, *key)
            if alive is not None:
                fills &= alive[key]
            if fills:
                nxt[key] = fills
        alive = nxt
        if not alive:
            return {}
    return alive or {}


def predict(grid, selector, placement, content, fill):
    """Output of one candidate on a grid, or None if the candidate is undefined there."""
    pair = _Pair(grid)
    if not _defined(pair, placement, content):
        return None
    mask = pair.selection(selector, placement)
    if mask is None:
        return None
    h, w = pair.h, pair.w
    out = [[fill] * (w * w) for _ in range(h * h)]
    for r in range(h):
        for c in range(w):
            if mask[r][c]:
                b = pair.block(placement, content, r, c)
                for y in range(h):
                    out[r * h + y][c * w:(c + 1) * w] = b[y]
    return out


def candidate_predictions(task_id, demonstrations, query_input, palette=None):
    """Distinct query predictions of all surviving candidates (None = undefined)."""
    if task_id not in TASK_IDS:
        raise ValueError(f'{task_id}: not a self-tiling family')
    seen, answers = set(), []
    query = _Pair(query_input)
    for (selector, placement, content), fills in surviving_candidates(demonstrations).items():
        mask = (query.selection(selector, placement)
                if _defined(query, placement, content) else None)
        needs_fill = mask is None or not all(all(r) for r in mask)
        for fill in (sorted(fills) if needs_fill else [min(fills)]):
            out = predict(query_input, selector, placement, content, fill)
            key = None if out is None else tuple(map(tuple, out))
            if key not in seen:
                seen.add(key)
                answers.append(out)
    return answers


def require_self_tiler_evidence(task_id, demonstrations, queries, palette=None):
    if not surviving_candidates(demonstrations):
        raise MissingColourEvidence(f'{task_id}: demonstrations fit no self-tiling candidate')
    for query in queries:
        answers = candidate_predictions(task_id, demonstrations, query['input'], palette)
        if len(answers) != 1:
            raise MissingColourEvidence(
                f'{task_id}: demonstrations leave the self-tiling query ambiguous')
        if answers[0] is None:
            raise MissingColourEvidence(
                f'{task_id}: every surviving self-tiling rule is undefined on the query')
