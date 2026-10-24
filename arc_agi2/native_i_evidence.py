"""Episode evidence for native batch I: 18447a8d and b4a43f3b (root-authorised, narrow).

Each gate enumerates a bounded, explicitly named set of competing rules. It
keeps the rules that reproduce EVERY demonstration output, and it requires
all survivors to give one defined answer on each query INPUT. Query answers
are never read. A competitor that is undefined on a demonstration (it needs a
tie-break) does not reproduce it. A surviving competitor that is undefined on
the query counts as disagreement.

This rules out the listed alternatives only. It does NOT claim the intended
rule is identifiable among all possible rules.

Grids are first returned to the native frame by undoing the episode's D4
geometry. Colours stay as shown, and roles come from the episode palette.
Each candidate set is closed under D4 conjugation, so the decision does not
depend on the transform.

* 18447a8d (background palette[7], locks palette[8]): bands are maximal runs
  of non-background rows. Each band has a left lock profile and one key
  colour with a right-anchored profile. Every candidate assigns a key to
  each band and draws it flush against that band's lock:
    - complement: the unique key whose row counts complete the lock to the
      common width (area / band rows). This is the native rule.
    - same_band; reverse; shift_down_s and shift_up_s for s = 1..6 (cyclic
      shifts of band order). These are order competitors.
    - area: the unique key whose cell count completes the lock's cell count.
      This is a colour-count competitor that ignores the row profile.
    - colour_ascending / colour_descending: keys dealt top to bottom in raw
      visible colour-number order. Both directions are included, so the set
      is D4-covariant. The verdict for one base scene CAN depend on the
      episode palette (seed 9 with two bands: ambiguous under the identity
      palette, accepted under [3,9,0,7,2,8,1,6,4,5]). That is the documented
      behaviour of this bounded family, not an invariance claim. A
      report-scoped ablation (reports/diversity-v1/native-batch-i/
      priority_ablation.py) compares it with all linear colour orders.
  Native witness: three 2-band demos whose keys already complete their own
  band leave same_band alive. A query with swapped keys is then rejected.
* b4a43f3b (background palette[0], separator palette[5], map palette[2]):
  in the native frame the top W x W block shows the motif, row W is the
  separator, and the map lies below. A candidate is a product of:
    - extraction: the top block downscaled to 3x3 (native), or by a fixed
      factor 1, 2 or 3;
    - motif D4 transform (8);
    - fill: native, motif zeros drawn in the map colour, or the motif
      silhouette in the map colour;
    - map D4 transform (8);
    - selector: marked, unmarked or all map cells.
  The output is evaluated separably: tile candidates x occupancy
  candidates. Native witness: three left-right symmetric motifs leave the
  mirrored motif alive. An asymmetric query motif is then rejected.
"""
import numpy as np

from .colour_evidence import MissingColourEvidence

KEY_LOCK_TASK = '18447a8d'
MOTIF_STAMP_TASK = 'b4a43f3b'
TASK_IDS = (KEY_LOCK_TASK, MOTIF_STAMP_TASK)
MAX_SHIFT = 6


def to_native(g, d4):
    """Undo the D4 geometry of augmentation.transformed (colours kept)."""
    a = np.array(g)
    a = np.rot90(a, d4 % 4)          # transformed rotates clockwise k times
    return a[:, ::-1] if d4 >= 4 else a


def from_native(a, d4):
    a = np.array(a)
    if d4 >= 4:
        a = a[:, ::-1]
    return np.rot90(a, -(d4 % 4))


def _d4(a, k):
    a = np.rot90(a, k % 4)
    return a[:, ::-1] if k >= 4 else a


# ------------------------------------------------------------------ 18447a8d
def _parse_bands(g, bg, lock):
    rows = [i for i in range(g.shape[0]) if (g[i] != bg).any()]
    bands = []
    for i in rows:
        if bands and i == bands[-1][-1] + 1:
            bands[-1].append(i)
        else:
            bands.append([i])
    locks, keys = [], []
    for b in bands:
        locks.append(tuple(int((g[i] == lock).sum()) for i in b))
        colours = {int(v) for i in b for v in g[i] if v not in (bg, lock)}
        if len(colours) != 1:
            return None
        c = colours.pop()
        keys.append((c, tuple(int((g[i] == c).sum()) for i in b)))
    return bands, locks, keys


def _key_assignments(g, bg, lock):
    """name -> assignment (band -> source key index) or None if undefined."""
    parsed = _parse_bands(g, bg, lock)
    if parsed is None:
        return None, {}
    bands, locks, keys = parsed
    n = len(bands)
    rows = sum(len(b) for b in bands)
    area = int((g != bg).sum())
    width = area // rows if rows and area % rows == 0 else None

    def unique(match):
        out = []
        for b in range(n):
            hits = [k for k in range(n) if match(b, k)]
            if len(hits) != 1:
                return None
            out.append(hits[0])
        return out if len(set(out)) == n else None

    def fits(b, k):
        return len(keys[k][1]) == len(locks[b]) and width is not None and all(
            x + y == width for x, y in zip(locks[b], keys[k][1]))

    cand = {'complement': unique(fits),
            'area': unique(lambda b, k: width is not None and
                           sum(keys[k][1]) == width * len(locks[b]) - sum(locks[b])),
            'same_band': list(range(n)),
            'reverse': [n - 1 - b for b in range(n)]}
    for s in range(1, MAX_SHIFT + 1):
        cand[f'shift_down_{s}'] = [(b - s) % n for b in range(n)]
        cand[f'shift_up_{s}'] = [(b + s) % n for b in range(n)]
    order = sorted(range(n), key=lambda k: keys[k][0])
    cand['colour_ascending'] = order
    cand['colour_descending'] = order[::-1]
    return (bands, locks, keys), cand


def _draw_keys(g, parsed, assignment, bg, lock):
    if assignment is None:
        return None
    bands, locks, keys = parsed
    out = np.where(g == lock, lock, bg)
    for b, k in enumerate(assignment):
        colour, profile = keys[k]
        if len(profile) != len(bands[b]):
            return None
        for row, lw, kw in zip(bands[b], locks[b], profile):
            if lw + kw > g.shape[1]:
                return None
            out[row, lw:lw + kw] = colour
    return out


def key_lock_predictions(grid, palette, d4):
    g = to_native(grid, d4)
    bg, lock = palette[7], palette[8]
    parsed, cand = _key_assignments(g, bg, lock)
    return {name: (None if parsed is None else _draw_keys(g, parsed, a, bg, lock))
            for name, a in cand.items()}


def _surviving_key_rules(demonstrations, palette, d4):
    alive = None
    for demo in demonstrations:
        want = to_native(demo['output'], d4)
        preds = key_lock_predictions(demo['input'], palette, d4)
        fit = {n for n, p in preds.items()
               if p is not None and p.shape == want.shape and (p == want).all()}
        alive = fit if alive is None else alive & fit
    return alive or set()


# ------------------------------------------------------------------ b4a43f3b
FILLS = ('native', 'zeros_to_mark', 'silhouette')
SELECTORS = ('marked', 'unmarked', 'all')
EXTRACTIONS = ('to_3x3', 'by_1', 'by_2', 'by_3')


def _parse_motif_map(g, sep):
    h, w = g.shape
    if h < w + 2 or not (g[w] == sep).all():
        return None
    return g[:w], g[w + 1:]


def _tiles(top, bg, mark):
    """(extraction, motif d4, fill) -> tile array or None."""
    w = top.shape[0]
    out = {}
    for e in EXTRACTIONS:
        f = w // 3 if e == 'to_3x3' else int(e[-1])
        if f < 1 or w % f or (e == 'to_3x3' and w % 3):
            base = None
        else:
            base = top[::f, ::f]
            blocks = np.kron(base, np.ones((f, f), dtype=base.dtype))
            if blocks.shape != top.shape or (blocks != top).any():
                base = None
        for k in range(8):
            for fill in FILLS:
                if base is None:
                    out[(e, k, fill)] = None
                    continue
                t = _d4(base, k).copy()
                if fill == 'zeros_to_mark':
                    t[t == bg] = mark
                elif fill == 'silhouette':
                    t[t != bg] = mark
                out[(e, k, fill)] = t
    return out


def _masks(mp, bg):
    """(map d4, selector) -> occupancy mask."""
    marked = mp != bg
    out = {}
    for k in range(8):
        m = _d4(marked, k)
        out[(k, 'marked')] = m
        out[(k, 'unmarked')] = ~m
        out[(k, 'all')] = np.ones_like(m)
    return out


def _stamp(tile, mask, bg):
    a = tile.shape[0]
    out = np.full((mask.shape[0] * a, mask.shape[1] * a), bg, dtype=tile.dtype)
    for i, j in zip(*np.nonzero(mask)):
        out[i * a:(i + 1) * a, j * a:(j + 1) * a] = tile
    return out


def _consistent_pairs(demo_in, demo_out, palette, d4):
    bg, sep, mark = palette[0], palette[5], palette[2]
    g, want = to_native(demo_in, d4), to_native(demo_out, d4)
    parsed = _parse_motif_map(g, sep)
    if parsed is None:
        return set()
    tiles, masks = _tiles(parsed[0], bg, mark), _masks(parsed[1], bg)
    by_mask = {}
    for qk, m in masks.items():
        by_mask.setdefault((m.shape, m.tobytes()), []).append(qk)
    pairs = set()
    by_tile = {}
    for tk, t in tiles.items():
        if t is not None:
            by_tile.setdefault((t.shape, t.tobytes()), []).append(tk)
    H, W = want.shape
    for (shape, _), tks in by_tile.items():
        t = tiles[tks[0]]
        a = shape[0]
        if H % a or W % a:
            continue
        p, q = H // a, W // a
        cells = want.reshape(p, a, q, a).transpose(0, 2, 1, 3)
        is_tile = (cells == t).all(axis=(2, 3))
        is_bg = (cells == bg).all(axis=(2, 3))
        if not (is_tile | is_bg).all():
            continue
        if (t == bg).all():
            qks = [qk for qk, m in masks.items() if m.shape == (p, q)]
        else:
            qks = by_mask.get(((p, q), is_tile.tobytes()), [])
        pairs.update((tk, qk) for tk in tks for qk in qks)
    return pairs


def motif_stamp_predictions(demonstrations, query_input, palette, d4):
    """Distinct native-frame predictions of the surviving candidates (None = undefined)."""
    alive = None
    for demo in demonstrations:
        fit = _consistent_pairs(demo['input'], demo['output'], palette, d4)
        alive = fit if alive is None else alive & fit
    if not alive:
        return alive or set(), []
    bg, sep, mark = palette[0], palette[5], palette[2]
    g = to_native(query_input, d4)
    parsed = _parse_motif_map(g, sep)
    if parsed is None:
        return alive, [None]
    tiles, masks = _tiles(parsed[0], bg, mark), _masks(parsed[1], bg)
    preds, seen = [], set()
    for tk, qk in alive:
        t, m = tiles[tk], masks[qk]
        key = None if t is None else (t.shape, t.tobytes(), m.shape, m.tobytes())
        if key in seen:
            continue
        seen.add(key)
        preds.append(None if t is None else _stamp(t, m, bg))
    return alive, preds


# --------------------------------------------------------------------- API
def surviving_rules(task_id, demonstrations, palette=None, d4=0):
    palette = list(range(10)) if palette is None else list(palette)
    if task_id == KEY_LOCK_TASK:
        return _surviving_key_rules(demonstrations, palette, d4)
    if task_id == MOTIF_STAMP_TASK:
        alive = None
        for demo in demonstrations:
            fit = _consistent_pairs(demo['input'], demo['output'], palette, d4)
            alive = fit if alive is None else alive & fit
        return alive or set()
    raise KeyError(task_id)


def candidate_predictions(task_id, demonstrations, query_input, palette=None, d4=0):
    """Distinct visible-frame answers of the surviving candidates; None = undefined."""
    palette = list(range(10)) if palette is None else list(palette)
    if task_id == KEY_LOCK_TASK:
        alive = _surviving_key_rules(demonstrations, palette, d4)
        preds = key_lock_predictions(query_input, palette, d4)
        native = [preds[n] for n in sorted(alive)]
    elif task_id == MOTIF_STAMP_TASK:
        _, native = motif_stamp_predictions(demonstrations, query_input, palette, d4)
    else:
        raise KeyError(task_id)
    out, seen = [], set()
    for p in native:
        v = None if p is None else from_native(p, d4).tolist()
        key = repr(v)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def require_native_i_evidence(task_id, demonstrations, queries, palette=None, d4=0):
    if not demonstrations:
        raise MissingColourEvidence(f'{task_id}: no demonstrations')
    if not surviving_rules(task_id, demonstrations, palette, d4):
        raise MissingColourEvidence(f'{task_id}: demonstrations fit no candidate rule')
    for query in queries:
        answers = candidate_predictions(task_id, demonstrations, query['input'], palette, d4)
        if len(answers) != 1 or answers[0] is None:
            raise MissingColourEvidence(f'{task_id}: demonstrations leave query rule ambiguous')
