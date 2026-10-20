"""Episode evidence for stamped rays, copied frames, and directional beams.

Inputs are demonstrations and query inputs only; query labels are never used.
These finite alternatives guard specific documented ambiguities, not all possible
rules consistent with a finite set of demonstrations.
"""
from collections import Counter
from .colour_evidence import (
    MissingColourEvidence, _colour_components, _require_rule_agreement,
)


def _vector(dr, dc, d4):
    if d4 >= 4: dc = -dc
    for _ in range(d4 % 4): dr, dc = dc, -dr
    return dr, dc


def require_spatial_evidence(task_id, demonstrations, queries, palette, d4):
    bg = palette[0]
    if task_id == 'ac605cbb':
        native = {1: ((0, 1), 2, (-1, 2)), 2: ((0, -1), 3, (0, -4)),
                  3: ((1, 0), 2, (3, 0)), 6: ((-1, 0), 5, (-6, 0))}
        stamps = {palette[k]: (_vector(*direction, d4), length, _vector(*copy, d4))
                  for k, (direction, length, copy) in native.items()}
        def scene(g):
            h, w = len(g), len(g[0])
            counts = Counter()
            out = [row[:] for row in g]
            seeds = [(r, c, ink) for r, row in enumerate(g) for c, ink in enumerate(row) if ink in stamps]
            for r, c, ink in seeds:
                (dy, dx), length, _ = stamps[ink]
                for step in range(1, length+1):
                    y, x = r+step*dy, c+step*dx
                    if 0 <= y < h and 0 <= x < w: counts[y, x] += 1
            for y, x in counts:
                if out[y][x] == bg: out[y][x] = palette[5]
            for r, c, ink in seeds:
                dy, dx = stamps[ink][2]
                if 0 <= r+dy < h and 0 <= c+dx < w: out[r+dy][c+dx] = ink
            return out, {p for p, n in counts.items() if n >= 2}, seeds
        required, seen = set(), set()
        crossing_needed, crossing_seen = False, False
        for q in queries:
            _, crosses, seeds = scene(q['input'])
            required.update(ink for _, _, ink in seeds)
            crossing_needed |= bool(crosses)
        for demo in demonstrations:
            _, crosses, seeds = scene(demo['input'])
            out = demo['output']
            for r, c, ink in seeds:
                dy, dx = stamps[ink][2]
                if 0 <= r+dy < len(out) and 0 <= c+dx < len(out[0]) and out[r+dy][c+dx] == ink:
                    seen.add(ink)
            crossing_seen |= any(out[r][c] == palette[4] for r, c in crosses)
        if required-seen or (crossing_needed and not crossing_seen):
            raise MissingColourEvidence('ac605cbb: missing seed stamp or crossing-colour evidence')
        def variants(g):
            base, crosses, _ = scene(g)
            outputs = []
            # Include crossing-only: a clipped ray need not teach propagation.
            for direction in [None, (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                out = [row[:] for row in base]
                for r, c in crosses:
                    out[r][c] = palette[4]
                    if direction is None: continue
                    dy, dx = direction
                    r, c = r+dy, c+dx
                    while 0 <= r < len(out) and 0 <= c < len(out[0]):
                        if out[r][c] == bg: out[r][c] = palette[4]
                        r, c = r+dy, c+dx
                outputs.append(out)
            return outputs
        _require_rule_agreement(task_id, demonstrations, queries, variants)
    elif task_id == 'dc2e9a9d':
        def copies(g):
            for cells in _colour_components(g, palette[3]):
                r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
                c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
                sides = [(0, -1, sum(r == r0 for r, c in cells)),
                         (0, 1, sum(r == r1 for r, c in cells)),
                         (1, -1, sum(c == c0 for r, c in cells)),
                         (1, 1, sum(c == c1 for r, c in cells))]
                nubs = [(axis, sign) for axis, sign, count in sides if count == 1]
                if len(nubs) != 1: raise MissingColourEvidence('dc2e9a9d: ambiguous nub side')
                axis, sign = nubs[0]
                targets = set()
                for r, c in cells:
                    y = r0+r1-r-sign*(r1-r0+2) if axis == 0 else r
                    x = c0+c1-c-sign*(c1-c0+2) if axis == 1 else c
                    if 0 <= y < len(g) and 0 <= x < len(g[0]): targets.add((y, x))
                if targets: yield axis, targets
        ink_for = {0: palette[1] if d4 % 2 else palette[8],
                   1: palette[8] if d4 % 2 else palette[1]}
        required, seen = set(), set()
        for query in queries: required.update(axis for axis, _ in copies(query['input']))
        for demo in demonstrations:
            for axis, cells in copies(demo['input']):
                if any(demo['output'][r][c] == ink_for[axis] for r, c in cells): seen.add(axis)
        if required-seen: raise MissingColourEvidence('dc2e9a9d: query nub-axis copy colour not demonstrated')
    elif task_id == 'db93a21d':
        def variants(g):
            h, w = len(g), len(g[0])
            boxes = []
            for cells in _colour_components(g, palette[9]):
                r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
                c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
                radius = max(r1-r0+1, c1-c0+1)//2
                boxes.append((r0, r1, c0, c1, radius))
            outputs = []
            for direction in range(4):  # down, left, up, right
                out = [row[:] for row in g]
                for r0, r1, c0, c1, rad in boxes:
                    rows, cols = [(range(r1+rad+1, h), range(c0, c1+1)),
                                  (range(r0, r1+1), range(0, max(0, c0-rad))),
                                  (range(0, max(0, r0-rad)), range(c0, c1+1)),
                                  (range(r0, r1+1), range(c1+rad+1, w))][direction]
                    for r in rows:
                        for c in cols: out[r][c] = palette[1]
                for r0, r1, c0, c1, rad in boxes:
                    for r in range(max(0, r0-rad), min(h, r1+rad+1)):
                        for c in range(max(0, c0-rad), min(w, c1+rad+1)): out[r][c] = palette[3]
                for r, row in enumerate(g):
                    for c, ink in enumerate(row):
                        if ink == palette[9]: out[r][c] = ink
                outputs.append(out)
            return outputs
        actual = lambda g: variants(g)[d4 % 4]
        if any(palette[1] in row for q in queries for row in actual(q['input'])):
            if not any(palette[1] in row for d in demonstrations for row in d['output']):
                raise MissingColourEvidence('db93a21d: query beam colour not demonstrated')
        _require_rule_agreement(task_id, demonstrations, queries, variants)
    else:
        raise ValueError('Unknown spatial evidence family: '+task_id)
