"""Episode evidence for 8ba14f53 (hole tally of two boxes), native batch G.

The gate enumerates a bounded, explicitly named set of tally rules, keeps the
rules that reproduce EVERY demonstration output, and requires all survivors to
give the same answer on each query INPUT. Query answers are never read. This
only rules out the listed alternatives; it is not a claim that the intended
rule is identifiable among all possible rules.

Native rule: each background region not touching the border is a hole, owned
by the one colour around it. Boxes are taken left to right. Each box writes
its colour once per hole cell into a 3x3 grid in row-major order, starting a
new row. Cells left over stay background.

Two boxes give only one bit of order per demonstration, so with three
demonstrations several order principles often fit the same context. This is
measured on the UNCHANGED native sampler too. A rule is one choice from each
factor:

* order (26): a spatial direction (left, right, top or bottom extreme of the
  box's cells), ties broken by either perpendicular direction (8); hole count
  descending or ascending, ties broken by any such direction pair (16);
  colour index ascending or descending (2);
* slot order (8): the eight D4 images of the row-major 3x3 sequence;
* layout (2): each box starts a new line of three, or runs continue;
* measure (2): hole cells, or the hole's bounding-box area (notch-blind).

That is 832 rules. The set is D4-closed, so no episode metadata is used
beyond the background palette[0]. An order whose whole key ties gives no
answer (boxes in disjoint column ranges never tie on both axes). Such a rule
cannot fit a demonstration; if it survives and is undefined on the query,
that counts as a distinct prediction (rejected).
A hole bordered by two colours, or none, is rejected outright.

Not enumerated: three or more boxes (never generated), counting box or
border cells (always overflows the 3x3 output), centre-based order (equal
to edge order for disjoint column ranges, the only native layout).
"""

TASK_ID = '8ba14f53'

_SPATIAL = {'L': lambda e: e[2], 'R': lambda e: -e[3],
            'T': lambda e: e[0], 'B': lambda e: -e[1]}
_PERP = {'L': 'TB', 'R': 'TB', 'T': 'LR', 'B': 'LR'}
ORDERS = (tuple(f'edge-{p}-tie-{s}' for p in 'LRTB' for s in _PERP[p])
          + tuple(f'count-{d}-tie-{t}-{s}' for d in ('desc', 'asc')
                  for t in 'LRTB' for s in _PERP[t])
          + ('colour-asc', 'colour-desc'))
_SQUARE = (lambda i, j: (i, j), lambda i, j: (j, i), lambda i, j: (2 - i, j),
           lambda i, j: (i, 2 - j), lambda i, j: (2 - i, 2 - j),
           lambda i, j: (2 - j, i), lambda i, j: (j, 2 - i),
           lambda i, j: (2 - j, 2 - i))
SLOT_ORDERS = tuple(tuple(f(i, j) for i in range(3) for j in range(3)) for f in _SQUARE)
LAYOUTS = ('new-row', 'continuous')
MEASURES = ('cells', 'bbox')
RULES = tuple((o, s, l, m) for o in ORDERS for s in range(len(SLOT_ORDERS))
              for l in LAYOUTS for m in MEASURES)
NATIVE_RULE = ('edge-L-tie-T', 0, 'new-row', 'cells')   # identity frame


def _missing(message):
    from .colour_evidence import MissingColourEvidence
    return MissingColourEvidence(f'{TASK_ID}: {message}')


def analyse(g, bg):
    """Per owner colour: hole cells, hole bounding-box area, cell extents."""
    g = [list(map(int, r)) for r in g]
    if not g or not g[0] or any(len(r) != len(g[0]) for r in g):
        raise _missing('malformed grid')
    h, w = len(g), len(g[0])
    seen, cells, area = set(), {}, {}
    for y in range(h):
        for x in range(w):
            if g[y][x] != bg or (y, x) in seen:
                continue
            seen.add((y, x))
            stack, region, touch, owners = [(y, x)], [], False, set()
            while stack:
                a, b = stack.pop()
                region.append((a, b))
                touch |= a in (0, h - 1) or b in (0, w - 1)
                for p, q in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= p < h and 0 <= q < w:
                        if g[p][q] == bg:
                            if (p, q) not in seen:
                                seen.add((p, q))
                                stack.append((p, q))
                        else:
                            owners.add(g[p][q])
            if touch:
                continue
            if len(owners) != 1:
                raise _missing('an enclosed background region has no single owner')
            c = owners.pop()
            ys = [a for a, _ in region]
            xs = [b for _, b in region]
            cells[c] = cells.get(c, 0) + len(region)
            area[c] = area.get(c, 0) + (max(ys) - min(ys) + 1) * (max(xs) - min(xs) + 1)
    extent = {}
    for c in cells:
        pts = [(y, x) for y in range(h) for x in range(w) if g[y][x] == c]
        extent[c] = (min(p[0] for p in pts), max(p[0] for p in pts),
                     min(p[1] for p in pts), max(p[1] for p in pts))
    return {'cells': cells, 'bbox': area}, extent


def _sequence(order, counts, extent):
    """Owner colours in rule order, or None for an unresolved tie."""
    colours = list(counts)
    if order.startswith('edge-'):
        _, p, _, s = order.split('-')
        key = lambda c: (_SPATIAL[p](extent[c]), _SPATIAL[s](extent[c]))
    elif order.startswith('count-'):
        _, d, _, t, s = order.split('-')
        sign = -1 if d == 'desc' else 1
        key = lambda c: (sign * counts[c], _SPATIAL[t](extent[c]), _SPATIAL[s](extent[c]))
    else:
        return tuple(sorted(colours, reverse=order == 'colour-desc'))
    keys = [key(c) for c in colours]
    if len(set(keys)) != len(keys):
        return None
    return tuple(sorted(colours, key=key))


def _render(seq, counts, slots, layout, bg):
    out = [[bg] * 3 for _ in range(3)]
    pos = 0
    for c in seq:
        n = counts[c]
        for i in range(n):
            if pos + i < 9:
                r, k = slots[pos + i]
                out[r][k] = c
        pos += -(-n // 3) * 3 if layout == 'new-row' else n
    return tuple(tuple(r) for r in out)


def variants(g, bg):
    """Output of every rule in RULES (None where the rule is undefined)."""
    measures, extent = analyse(g, bg)
    cache, result = {}, []
    for order, slot, layout, measure in RULES:
        counts = measures[measure]
        seq = _sequence(order, counts, extent)
        key = (seq, slot, layout, measure)
        if key not in cache:
            cache[key] = None if seq is None else _render(seq, counts, SLOT_ORDERS[slot], layout, bg)
        result.append(cache[key])
    return result


def surviving_rules(demonstrations, palette=None):
    bg = (list(range(10)) if palette is None else list(palette))[0]
    alive = set(range(len(RULES)))
    for demo in demonstrations:
        target = tuple(tuple(int(v) for v in r) for r in demo['output'])
        alive &= {i for i, out in enumerate(variants(demo['input'], bg)) if out == target}
        if not alive:
            break
    return alive


def candidate_predictions(demonstrations, query_input, palette=None):
    """Distinct query answers (None = undefined) of rules fitting every demo."""
    bg = (list(range(10)) if palette is None else list(palette))[0]
    alive = surviving_rules(demonstrations, palette)
    options = variants(query_input, bg)
    answers = []
    for i in sorted(alive):
        if options[i] not in answers:
            answers.append(options[i])
    return answers


def require_hole_tally_evidence(demonstrations, queries, palette=None):
    """Raise MissingColourEvidence unless every surviving rule agrees per query."""
    if not surviving_rules(demonstrations, palette):
        raise _missing('demonstrations fit no candidate rule')
    for query in queries:
        if len(candidate_predictions(demonstrations, query['input'], palette)) > 1:
            raise _missing('demonstrations leave query rule ambiguous')
