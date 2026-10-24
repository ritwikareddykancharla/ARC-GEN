"""Episode evidence for cell-aligned panel overlay families (native batch D).

Root-authorised narrow gates for four families only:

* 281123b4: four equal panels split by three full separator lines (native 3);
  panel colours 8, 5, 9, 4 overlay by priority. All 24 priority orders of the
  four visible panel colours are enumerated; the orders reproducing EVERY
  demonstration output are kept, and every surviving order must predict the
  same answer for each query.
* 195ba7dc (OR, separator 2), 34b99a2b (XOR, separator 4): two equal panels
  split by one full separator line.
* 31d5ba1a (XOR): two equal halves stacked without a separator; the split axis
  follows the episode D4 transform exactly as in the direct factory.

For the Boolean families each answer cell is f(a, b) of the ordered panel
occupancies (a, b) (occupied = not background). Every truth table consistent
with ALL demonstration labels must agree on the query; equivalently, every
occupancy combination present in the query must have been observed in the
demonstrations, always with the same outcome.

Only demonstration answers and query INPUTS are read. Everything is computed
in visible coordinates: D4 transforms keep panels cell-aligned translated
copies (panel order may flip, consistently for the whole episode), and the
role colours come from the episode palette.
"""
from itertools import permutations

PRIORITY_TASK = '281123b4'
NATIVE_PANEL_COLOURS = (8, 5, 9, 4)
ORDERS = tuple(permutations(range(4)))  # indices into panel colours, highest first
# task id -> native separator colour (None: halves without a separator)
BOOLEAN_TASKS = {'195ba7dc': 2, '34b99a2b': 4, '31d5ba1a': None}
TASK_IDS = (PRIORITY_TASK,) + tuple(BOOLEAN_TASKS)


def _missing(task_id, message):
    from .colour_evidence import MissingColourEvidence
    return MissingColourEvidence(f'{task_id}: {message}')


def _rows(task_id, grid):
    rows = [list(r) for r in grid]
    if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
        raise _missing(task_id, 'malformed input grid')
    return rows


def split_panels(task_id, grid, palette, d4=0, count=2):
    """Return equal visible panels of an input, in visible order."""
    rows = _rows(task_id, grid)
    h, w = len(rows), len(rows[0])
    cols_of = lambda a, b: [r[a:b] for r in rows]
    rows_of = lambda a, b: [r[:] for r in rows[a:b]]
    sep_native = 3 if task_id == PRIORITY_TASK else BOOLEAN_TASKS[task_id]
    if sep_native is None:
        across_columns = (d4 % 4) % 2 == 1   # native vertical stack, transposed
        n = w if across_columns else h
        if n % 2:
            raise _missing(task_id, 'odd extent cannot hold two equal halves')
        take = cols_of if across_columns else rows_of
        parts = [take(0, n // 2), take(n // 2, n)]
    else:
        sep = palette[sep_native]
        full_cols = [x for x in range(w) if all(r[x] == sep for r in rows)]
        full_rows = [y for y in range(h) if all(v == sep for v in rows[y])]
        if len(full_cols) == count - 1 and not full_rows:
            cuts, n, take = full_cols, w, cols_of
        elif len(full_rows) == count - 1 and not full_cols:
            cuts, n, take = full_rows, h, rows_of
        else:
            raise _missing(task_id, f'input lacks exactly {count - 1} full separator line(s)')
        bounds = [-1] + cuts + [n]
        parts = [take(a + 1, b) for a, b in zip(bounds, bounds[1:])]
    if any(not p or not p[0] for p in parts) or len({(len(p), len(p[0])) for p in parts}) != 1:
        raise _missing(task_id, 'input does not split into equal non-empty panels')
    return parts


# ------------------------------------------------------------------ 281123b4

def priority_predictions(grid, palette=None, task_id=PRIORITY_TASK):
    """Answer predicted by each of the 24 priority orders (tuple of tuples)."""
    palette = list(range(10)) if palette is None else list(palette)
    bg, colours = palette[0], tuple(palette[c] for c in NATIVE_PANEL_COLOURS)
    parts = split_panels(task_id, grid, palette, count=4)
    if any(v not in set(colours) | {bg} for p in parts for r in p for v in r):
        raise _missing(task_id, 'panel holds a colour outside background and panel colours')
    h, w = len(parts[0]), len(parts[0][0])
    present = [[{p[y][x] for p in parts} - {bg} for x in range(w)] for y in range(h)]
    result = []
    for order in ORDERS:
        rank = {colours[i]: k for k, i in enumerate(order)}
        result.append(tuple(tuple(min(cell, key=rank.__getitem__) if cell else bg
                                  for cell in row) for row in present))
    return result


def surviving_orders(demonstrations, palette=None):
    """Indices into ORDERS reproducing every demonstration output."""
    alive = set(range(len(ORDERS)))
    for demo in demonstrations:
        target = tuple(tuple(r) for r in demo['output'])
        alive &= {i for i, out in enumerate(priority_predictions(demo['input'], palette))
                  if out == target}
    return alive


def require_priority_evidence(demonstrations, queries, palette=None):
    alive = surviving_orders(demonstrations, palette)
    if not alive:
        raise _missing(PRIORITY_TASK, 'demonstrations fit no panel priority order')
    for query in queries:
        options = priority_predictions(query['input'], palette)  # query INPUT only
        if len({options[i] for i in alive}) != 1:
            raise _missing(PRIORITY_TASK, 'demonstrations leave the query panel priority unresolved')


# --------------------------------------------- 195ba7dc, 31d5ba1a, 34b99a2b

def occupancy(task_id, grid, palette=None, d4=0):
    """Grid of ordered (a, b) panel occupancies of a visible input."""
    palette = list(range(10)) if palette is None else list(palette)
    a, b = split_panels(task_id, grid, palette, d4)
    bg = palette[0]
    return [[(int(x != bg), int(y != bg)) for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def observed_truth_table(task_id, demonstrations, palette=None, d4=0):
    """Occupancy combination -> demonstrated outcome; raises if no table fits."""
    table = {}
    for demo in demonstrations:
        occ = occupancy(task_id, demo['input'], palette, d4)
        out = demo['output']
        if len(out) != len(occ) or any(len(r) != len(occ[0]) for r in out):
            raise _missing(task_id, 'demonstration output is not one panel in size')
        for orow, vrow in zip(occ, out):
            for combo, value in zip(orow, vrow):
                if table.setdefault(combo, value) != value:
                    raise _missing(task_id, 'demonstrations fit no Boolean truth table')
    return table


def predict_from_table(task_id, table, grid, palette=None, d4=0):
    """Unique answer of all consistent truth tables, or None if they disagree."""
    occ = occupancy(task_id, grid, palette, d4)
    if any(combo not in table for row in occ for combo in row):
        return None
    return [[table[combo] for combo in row] for row in occ]


def require_occupancy_evidence(task_id, demonstrations, queries, palette=None, d4=0):
    table = observed_truth_table(task_id, demonstrations, palette, d4)
    for query in queries:
        if predict_from_table(task_id, table, query['input'], palette, d4) is None:
            raise _missing(task_id, 'query has a panel occupancy combination the '
                                    'demonstrations never resolve')


def require_panel_overlay_evidence(task_id, demonstrations, queries, palette=None, d4=0):
    if task_id == PRIORITY_TASK:
        require_priority_evidence(demonstrations, queries, palette)
    elif task_id in BOOLEAN_TASKS:
        require_occupancy_evidence(task_id, demonstrations, queries, palette, d4)
    else:
        raise ValueError(task_id + ': not a reviewed panel overlay family')
