"""Visible-input solver for ARC task d6542281.

Reads only the input grid.

Objects. The background is the strict plurality colour. Non-background cells
are split into 8-connected components. Multicoloured components are
templates, and single-coloured components are fragments.

Candidates. A candidate stamp is a translated copy of a template that lines
up one fragment's anchor cell with a template cell of the same colour. A
candidate is admissible when:
  * its footprint lies in the grid;
  * it neither overlaps nor 8-touches a template;
  * every non-background cell under it is a fragment cell of the same colour;
  * every fragment component it meets lies wholly inside it.

Arrangements. A full arrangement picks admissible stamps that cover every
fragment component exactly once, with no two footprints overlapping or
8-touching. Siblings are therefore resolved jointly: a stamp that covers a
fragment must also explain every other fragment under its footprint.

Outcome. The search is exhaustive within a node budget. If it finds no
arrangement, finds several, or runs out of budget, transform raises
ValueError instead of guessing. Otherwise the output is the input with every
non-background colour that occurs exactly once erased to background, and then
every chosen stamp is drawn in full.
"""

from collections import Counter

_NEIGH = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0),
          (1, 1))
_NODE_BUDGET = 200000
_CANDIDATE_LIMIT = 50000


class _BudgetExhausted(Exception):
    pass


def _components(cells):
    seen, out = set(), []
    for p in sorted(cells):
        if p in seen:
            continue
        seen.add(p)
        stack, comp = [p], []
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in _NEIGH:
                q = (r + dr, c + dc)
                if q in cells and q not in seen:
                    seen.add(q)
                    stack.append(q)
        out.append(frozenset(comp))
    return out


def _halo(cells):
    h = set(cells)
    for r, c in cells:
        for dr, dc in _NEIGH:
            h.add((r + dr, c + dc))
    return h


def _background(rows):
    counts = Counter(v for row in rows for v in row)
    ranked = counts.most_common(2)
    if len(ranked) == 2 and ranked[0][1] == ranked[1][1]:
        raise ValueError('no strict plurality background colour')
    return ranked[0][0], counts


def _cover(foot, height, width, blocked, frag_colour, comp_of, frags):
    cover = set()
    for (r, c), v in foot.items():
        if not (0 <= r < height and 0 <= c < width):
            return None
        if (r, c) in blocked:
            return None
        if (r, c) in frag_colour:
            if frag_colour[(r, c)] != v:
                return None
            cover.add(comp_of[(r, c)])
    for k in cover:
        if any(q not in foot for q in frags[k]):
            return None
    return frozenset(cover) if cover else None


def _search(n, options, stamps):
    solutions = []
    nodes = [0]

    def rec(covered, chosen):
        nodes[0] += 1
        if nodes[0] > _NODE_BUDGET:
            raise _BudgetExhausted()
        if len(covered) == n:
            solutions.append(tuple(chosen))
            return len(solutions) >= 2
        best = None
        for k in range(n):
            if k in covered:
                continue
            live = []
            for s in options[k]:
                if not stamps[s][3].isdisjoint(covered):
                    continue
                halo = stamps[s][2]
                if any(not halo.isdisjoint(stamps[o][1]) for o in chosen):
                    continue
                live.append(s)
            if not live:
                return False
            if best is None or len(live) < len(best):
                best = live
        for s in best:
            chosen.append(s)
            if rec(covered | stamps[s][3], chosen):
                return True
            chosen.pop()
        return False

    try:
        rec(frozenset(), [])
    except _BudgetExhausted:
        raise ValueError('arrangement search budget exhausted; uniqueness '
                         'not certified') from None
    return solutions


def transform(grid):
    rows = [[int(v) for v in row] for row in grid]
    height = len(rows)
    if height == 0:
        raise ValueError('empty grid')
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError('grid must be a non-empty rectangle')
    bg, counts = _background(rows)
    cells = {(r, c): rows[r][c] for r in range(height) for c in range(width)
             if rows[r][c] != bg}
    templates, frags, blocked = [], [], set()
    for comp in _components(cells):
        if len({cells[p] for p in comp}) > 1:
            r0 = min(r for r, _ in comp)
            c0 = min(c for _, c in comp)
            templates.append(tuple(sorted(((r - r0, c - c0), cells[(r, c)])
                                          for r, c in comp)))
            blocked |= _halo(comp)
        else:
            frags.append(comp)
    frag_colour, comp_of = {}, {}
    for k, comp in enumerate(frags):
        for p in comp:
            frag_colour[p] = cells[p]
            comp_of[p] = k
    stamps, seen = [], set()
    options = [[] for _ in frags]
    for comp in frags:
        r0, c0 = min(comp)
        colour = cells[(r0, c0)]
        for tmpl in templates:
            for (tr, tc), tcol in tmpl:
                if tcol != colour:
                    continue
                dr, dc = r0 - tr, c0 - tc
                foot = {(r + dr, c + dc): v for (r, c), v in tmpl}
                key = frozenset(foot.items())
                if key in seen:
                    continue
                seen.add(key)
                if len(seen) > _CANDIDATE_LIMIT:
                    raise ValueError('too many candidate stamps; scene not '
                                     'certified')
                cover = _cover(foot, height, width, blocked, frag_colour,
                               comp_of, frags)
                if cover is None:
                    continue
                sid = len(stamps)
                stamps.append((foot, frozenset(foot), _halo(foot), cover))
                for kk in cover:
                    options[kk].append(sid)
    solutions = _search(len(frags), options, stamps)
    if not solutions:
        raise ValueError('no consistent arrangement of the fragments')
    if len(solutions) > 1:
        raise ValueError('ambiguous scene: several fragment arrangements')
    out = [row[:] for row in rows]
    singles = {v for v, n in counts.items() if v != bg and n == 1}
    if singles:
        for r in range(height):
            for c in range(width):
                if out[r][c] in singles:
                    out[r][c] = bg
    for s in solutions[0]:
        for (r, c), v in stamps[s][0].items():
            out[r][c] = int(v)
    return out
