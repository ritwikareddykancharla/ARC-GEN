"""Require visible demonstration evidence for arbitrary colour associations.

These checks consume demonstration answers and query inputs only. They do not
attempt to prove every ARC rule identifiable from finitely many examples.
"""


class MissingColourEvidence(ValueError):
    pass


def require_colour_evidence(task_id, demonstrations, queries, palette=None, d4=0):
    if task_id not in ('6ea4a07e', '913fb3ed', '494ef9d7', '995c5fa3',
                       'a834deea', 'a9f96cdd', 'a416fc5b', 'a740d043',
                       'a6953f00', 'aaecdb9a', 'a68b268e'):
        return
    palette = list(range(10)) if palette is None else palette
    bg = palette[0]
    colours = lambda g: {c for row in g for c in row} - {bg}
    required, seen = set(), set()
    if task_id == '6ea4a07e':
        for demo in demonstrations:
            # A completely filled mask has an all-background output and reveals
            # nothing about the colour that would fill the complement.
            if any(bg in row for row in demo['input']) and colours(demo['output']):
                seen.update(colours(demo['input']))
        for query in queries:
            if any(bg in row for row in query['input']):
                required.update(colours(query['input']))
    elif task_id == '913fb3ed':
        for demo in demonstrations:
            a, b = demo['input'], demo['output']
            for r, row in enumerate(a):
                for c, ink in enumerate(row):
                    if ink == bg:
                        continue
                    # An isolated seed demonstrates its mapping only if a
                    # formerly blank neighbouring cell acquires ring colour.
                    if any(0 <= r+dr < len(a) and 0 <= c+dc < len(row)
                           and a[r+dr][c+dc] == bg and b[r+dr][c+dc] != bg
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                           if dr or dc):
                        seen.add(ink)
        for query in queries:
            required.update(colours(query['input']))
    elif task_id == '995c5fa3':
        def panel_keys(g):
            # Three visible 4x4 panels, with one-cell separators. An odd D4
            # quarter-turn stacks them vertically instead of horizontally.
            for start in (0, 5, 10):
                yield frozenset((r, c) for r in range(4) for c in range(4)
                                if (g[start+r][c] if d4 % 2
                                    else g[r][start+c]) == bg)
        for demo in demonstrations:
            seen.update(panel_keys(demo['input']))
        for query in queries:
            required.update(panel_keys(query['input']))
    elif task_id == 'a6953f00':
        # The selected corner differs for odd/even square sides.
        seen.update(len(d['input']) % 2 for d in demonstrations)
        required.update(len(q['input']) % 2 for q in queries)
    elif task_id == 'aaecdb9a':
        legend = {palette[c] for c in (5, 2, 8, 9, 6)}
        for demo in demonstrations:
            seen.update(c for row in demo['output'] for c in row if c in legend)
        for query in queries:
            required.update(c for row in query['input'] for c in row if c in legend)
    elif task_id == 'a68b268e':
        # The four panels share a coordinate system. A demonstrated overlap
        # establishes winner > loser; transitive precedence is also evidence.
        edges = set()
        def overlays(g):
            for r in range(4):
                for c in range(4):
                    yield r, c, {g[y+r][x+c] for y in (0, 5) for x in (0, 5)} - {bg}
        for demo in demonstrations:
            for r, c, inks in overlays(demo['input']):
                winner = demo['output'][r][c]
                if winner in inks:
                    edges.update((winner, ink) for ink in inks if ink != winner)
        while True:
            closure = edges | {(a, d) for a, b in edges for c, d in edges if b == c}
            if closure == edges:
                break
            edges = closure
        for query in queries:
            for r, c, inks in overlays(query['input']):
                for a in inks:
                    for b in inks:
                        if a < b:
                            required.add((a, b))
                            if (a, b) in edges or (b, a) in edges:
                                seen.add((a, b))
    elif task_id == 'a834deea':
        def slots(g):
            # The connected outer border identifies each five-cell square.
            # Interior zeros may be disconnected; inspect the whole square.
            visited = set()
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink != bg or (r, c) in visited:
                        continue
                    cells, stack = [], [(r, c)]
                    visited.add((r, c))
                    while stack:
                        y, x = stack.pop()
                        cells.append((y, x))
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            p = y+dy, x+dx
                            if (0 <= p[0] < len(g) and 0 <= p[1] < len(row)
                                    and p not in visited and g[p[0]][p[1]] == bg):
                                visited.add(p)
                                stack.append(p)
                    y0 = min(y for y, x in cells)
                    x0 = min(x for y, x in cells)
                    if (max(y for y, x in cells)-y0 != 4
                            or max(x for y, x in cells)-x0 != 4):
                        continue
                    if not all(g[y0+y][x0+x] == bg for y in range(5)
                               for x in range(5) if y in (0, 4) or x in (0, 4)):
                        continue
                    for y in range(1, 4):
                        for x in range(1, 4):
                            if (y, x) != (2, 2) and g[y0+y][x0+x] == bg:
                                yield (y, x), (y0+y, x0+x)
        for demo in demonstrations:
            for key, (r, c) in slots(demo['input']):
                if demo['output'][r][c] != bg:
                    seen.add(key)
        for query in queries:
            required.update(key for key, _ in slots(query['input']))
    elif task_id == 'a9f96cdd':
        def diagonals(g):
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink == palette[2]:
                        for dy, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                            if 0 <= r+dy < len(g) and 0 <= c+dx < len(row):
                                yield (dy, dx), (r+dy, c+dx)
        for demo in demonstrations:
            for key, (r, c) in diagonals(demo['input']):
                if demo['output'][r][c] != bg:
                    seen.add(key)
        for query in queries:
            required.update(key for key, _ in diagonals(query['input']))
    elif task_id == 'a416fc5b':
        def solved(g):
            return any(c in (palette[5], palette[8]) for row in g for c in row)
        for demo in demonstrations:
            out = demo['output']
            if (solved(demo['input']) and len(out) == 16
                    and all(len(row) == 16 and all(c == palette[7] for c in row)
                            for row in out)):
                seen.add('solved-board-to-blank')
        if any(solved(q['input']) for q in queries):
            required.add('solved-board-to-blank')
    elif task_id == 'a740d043':
        def crop_has_holes(g):
            pixels = [(r, c) for r, row in enumerate(g)
                      for c, ink in enumerate(row) if ink != palette[1]]
            if not pixels:
                return False
            rows, cols = zip(*pixels)
            return any(g[r][c] == palette[1]
                       for r in range(min(rows), max(rows)+1)
                       for c in range(min(cols), max(cols)+1))
        for demo in demonstrations:
            if crop_has_holes(demo['input']) and any(bg in row for row in demo['output']):
                seen.add('crop-hole-fill')
        if any(crop_has_holes(q['input']) for q in queries):
            required.add('crop-hole-fill')
    else:
        active = {frozenset((palette[4], palette[7])),
                  frozenset((palette[1], palette[8]))}
        def lines(g):
            return list(zip(*g)) if d4 % 2 else g
        def key(line):
            cells = [(i, c) for i, c in enumerate(line) if c != bg]
            if len(cells) != 2 or cells[1][0] - cells[0][0] <= 1:
                return None
            pair = frozenset(c for _, c in cells)
            return pair if pair in active else None
        for demo in demonstrations:
            for a, b in zip(lines(demo['input']), lines(demo['output'])):
                pair = key(a)
                if pair is not None and list(a) != list(b):
                    seen.add(pair)
        for query in queries:
            required.update(pair for line in lines(query['input'])
                            if (pair := key(line)) is not None)
    missing = required - seen
    if missing:
        raise MissingColourEvidence(
            f'{task_id}: query requires {len(missing)} colour association(s) '
            'not demonstrated in the context')
