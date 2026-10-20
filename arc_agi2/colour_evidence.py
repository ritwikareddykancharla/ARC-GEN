"""Require visible demonstration evidence for arbitrary colour associations.

These checks consume demonstration answers and query inputs only. They do not
attempt to prove every ARC rule identifiable from finitely many examples.
"""


class MissingColourEvidence(ValueError):
    pass


def _require_rule_agreement(task_id, demonstrations, queries, variants):
    """Keep rules fitting demonstrations; compare them on the SAME query input."""
    possible = None
    for demo in demonstrations:
        fitted = {i for i, out in enumerate(variants(demo['input']))
                  if out == demo['output']}
        possible = fitted if possible is None else possible & fitted
    if not possible:
        raise MissingColourEvidence(f'{task_id}: demonstrations fit no candidate rule')
    for query in queries:
        options = variants(query['input'])
        predictions = {tuple(tuple(row) for row in options[i]) for i in possible}
        if len(predictions) > 1:
            raise MissingColourEvidence(f'{task_id}: demonstrations leave query rule ambiguous')


def _colour_components(g, colour):
    remaining = {(r, c) for r, row in enumerate(g) for c, ink in enumerate(row)
                 if ink == colour}
    while remaining:
        component = {remaining.pop()}
        stack = list(component)
        while stack:
            r, c = stack.pop()
            for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                if p in remaining:
                    remaining.remove(p)
                    component.add(p)
                    stack.append(p)
        yield component


def _hole_count(cells):
    """Count bounded four-connected empty regions inside an object's box."""
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    remaining = {(r, c) for r in range(top, bottom+1)
                 for c in range(left, right+1)} - set(cells)
    holes = 0
    while remaining:
        stack = [remaining.pop()]
        touches = False
        while stack:
            r, c = stack.pop()
            touches |= r in (top, bottom) or c in (left, right)
            for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                if p in remaining:
                    remaining.remove(p)
                    stack.append(p)
        holes += not touches
    return holes


def require_colour_evidence(task_id, demonstrations, queries, palette=None, d4=0):
    if task_id not in ('6ea4a07e', '913fb3ed', '494ef9d7', '995c5fa3',
                       'a834deea', 'a9f96cdd', 'a416fc5b', 'a740d043',
                       'a6953f00', 'aaecdb9a', 'a68b268e',
                       'c0f76784', 'bcb3040b', 'c8b7cc0f', 'c8f0f002',
                       'b1948b0a', 'c1d99e64', 'cce03e0d', 'c9e6f938',
                       'c61be7dc', 'd0f5fe59', 'd037b0a7', 'd23f8c26',
                       'd406998b', 'd2acf2cb', 'cf98881b', 'd511f180',
                       'd631b094', 'd5d6de2d', 'd90796e8', 'd364b489',
                       'dbc1a6ce', 'dc1df850', 'dd6b8c4b', 'dce56571',
                       'e45ef808', 'e345f17b', 'e3497940',
                       'e760a62e', 'e8593010', 'e99362f0', 'e6de6e8f',
                       '37d3e8b2'):
        return
    palette = list(range(10)) if palette is None else palette
    bg = palette[0]
    colours = lambda g: {c for row in g for c in row} - {bg}
    required, seen = set(), set()
    if task_id == '37d3e8b2':
        mapping = {1: palette[1], 2: palette[2], 3: palette[3], 4: palette[7]}
        for demo in demonstrations:
            for cells in _colour_components(demo['input'], palette[8]):
                n = _hole_count(cells)
                if n in mapping and all(demo['output'][r][c] == mapping[n]
                                        for r, c in cells):
                    seen.add(n)
        for query in queries:
            required.update(_hole_count(cells) for cells in
                            _colour_components(query['input'], palette[8]))
    elif task_id == 'e6de6e8f':
        def commands(g):
            for cells in _colour_components(g, palette[2]):
                y0, x0 = min(r for r, c in cells), min(c for r, c in cells)
                yield frozenset((r-y0, c-x0) for r, c in cells)
        for demo in demonstrations:
            seen.update(commands(demo['input']))
        for query in queries:
            required.update(commands(query['input']))
    elif task_id == 'e8593010':
        for demo in demonstrations:
            for cells in _colour_components(demo['input'], palette[0]):
                n = len(cells)
                if n in (1, 2, 3) and all(demo['output'][r][c] == palette[4-n]
                                         for r, c in cells):
                    seen.add(n)
        for query in queries:
            required.update(len(cells) for cells in _colour_components(query['input'], palette[0]))
    elif task_id == 'e760a62e':
        def crosses(g):
            def bands(lines):
                groups, index = {}, -1
                previous_divider = True
                for i, line in enumerate(lines):
                    divider = all(ink == palette[8] for ink in line)
                    if not divider:
                        if previous_divider:
                            index += 1
                        groups[i] = index
                    previous_divider = divider
                return groups
            rows, cols = bands(g), bands(zip(*g))
            markers = {}
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if r in rows and c in cols and ink not in (bg, palette[8]):
                        markers.setdefault(ink, set()).add((rows[r], cols[c]))
            covered = {}
            for ink, points in markers.items():
                for r, c in points:
                    covered.setdefault((r, c), set()).add(ink)
                    for y, x in points:
                        if r == y:
                            for column in range(min(c, x), max(c, x)+1):
                                covered.setdefault((r, column), set()).add(ink)
                        if c == x:
                            for row in range(min(r, y), max(r, y)+1):
                                covered.setdefault((row, c), set()).add(ink)
            return any(len(inks) > 1 for inks in covered.values())
        if any(crosses(q['input']) for q in queries):
            required.add('crossing-colour')
        if any(crosses(d['input']) and any(palette[6] in row for row in d['output'])
               for d in demonstrations):
            seen.add('crossing-colour')
    elif task_id == 'e45ef808':
        def ties(g):
            lines = list(g) if d4 % 2 else list(zip(*g))
            heights = [sum(c == palette[6] for c in line) for line in lines]
            return {name for name, height in (('peak-tie', max(heights)),
                                              ('valley-tie', min(heights)))
                    if heights.count(height) > 1}
        for demo in demonstrations:
            seen.update(ties(demo['input']))
        for query in queries:
            required.update(ties(query['input']))
    elif task_id == 'e345f17b':
        def has_nor(g):
            if d4 % 2:
                half = len(g)//2
                return any(a == b == bg for x, y in zip(g[:half], g[half:])
                           for a, b in zip(x, y))
            half = len(g[0])//2
            return any(row[c] == row[c+half] == bg for row in g for c in range(half))
        if any(has_nor(q['input']) for q in queries):
            required.add('nor-mark-colour')
        if any(has_nor(d['input']) and any(palette[4] in row for row in d['output'])
               for d in demonstrations):
            seen.add('nor-mark-colour')
    elif task_id == 'e3497940':
        def variants(g):
            if d4 % 2:
                mid = len(g)//2
                first, second = g[:mid], g[mid+1:][::-1]
                merged = [[b if b != bg else a for a, b in zip(x, y)]
                          for x, y in zip(first, second)]
                return [merged, merged[::-1]]
            mid = len(g[0])//2
            merged = [[b if b != bg else a for a, b in zip(row[:mid], row[mid+1:][::-1])]
                      for row in g]
            return [merged, [row[::-1] for row in merged]]
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'dd6b8c4b':
        from .augmentation import transformed
        orders = []
        for orientation in range(8):
            indices = transformed([[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                                  orientation, list(range(10)))
            orders.append(sorted(((r-1, c-1) for r in range(3) for c in range(3)),
                                 key=lambda p: indices[p[0]+1][p[1]+1]))
        def tank(g):
            cores = [(r, c) for r, row in enumerate(g) for c, ink in enumerate(row)
                     if ink == palette[2]]
            if len(cores) != 1:
                raise MissingColourEvidence(f'{task_id}: expected one visible tank core')
            cy, cx = cores[0]
            cells = {(cy+dr, cx+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            reached, stack = set(cells), list(cells)
            while stack:
                r, c = stack.pop()
                for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                    if (0 <= p[0] < len(g) and 0 <= p[1] < len(g[0])
                            and p not in reached and g[p[0]][p[1]] != palette[6]):
                        reached.add(p)
                        stack.append(p)
            count = min(9, sum(g[r][c] == palette[9] for r, c in reached-cells))
            return cy, cx, count
        possible = set(range(8))
        for demo in demonstrations:
            cy, cx, count = tank(demo['input'])
            observed = {(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if demo['output'][cy+dr][cx+dc] == palette[9]}
            possible &= {i for i, order in enumerate(orders) if set(order[:count]) == observed}
        if not possible:
            raise MissingColourEvidence(f'{task_id}: demonstrations fit no tank fill order')
        for query in queries:
            _, _, count = tank(query['input'])
            if len({frozenset(orders[i][:count]) for i in possible}) > 1:
                raise MissingColourEvidence(f'{task_id}: demonstrations leave tank fill order ambiguous')
        return
    elif task_id == 'dce56571':
        # The input/background role is 8 here, unlike the common zero canvas.
        if any(sum(c != palette[8] for row in q['input'] for c in row) > 1 for q in queries):
            required.add('centred-line-axis')
        if any(sum(c != palette[8] for row in d['input'] for c in row) > 1 for d in demonstrations):
            seen.add('centred-line-axis')
    elif task_id == 'dc1df850':
        def paints(g):
            return any(0 <= r+dr < len(g) and 0 <= c+dc < len(row)
                       and g[r+dr][c+dc] == bg
                       for r, row in enumerate(g) for c, ink in enumerate(row)
                       if ink == palette[2]
                       for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
        if any(paints(q['input']) for q in queries):
            required.add('seed-ring-colour')
        if any(paints(d['input']) and any(palette[1] in row for row in d['output'])
               for d in demonstrations):
            seen.add('seed-ring-colour')
    elif task_id == 'dbc1a6ce':
        def bridge(g):
            for line in list(g)+[list(col) for col in zip(*g)]:
                dots = [i for i, ink in enumerate(line) if ink == palette[1]]
                if len(dots) > 1 and any(line[i] == bg for i in range(dots[0]+1, dots[-1])):
                    return True
            return False
        if any(bridge(q['input']) for q in queries):
            required.add('bridge-fill-colour')
        if any(bridge(d['input']) and any(palette[8] in row for row in d['output'])
               for d in demonstrations):
            seen.add('bridge-fill-colour')
    elif task_id == 'd364b489':
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
        def seed_neighbours(g):
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink == palette[1]:
                        for dr, dc in directions:
                            if 0 <= r+dr < len(g) and 0 <= c+dc < len(row):
                                yield dr, dc, r+dr, c+dc
        for demo in demonstrations:
            for dr, dc, r, c in seed_neighbours(demo['input']):
                if demo['output'][r][c] not in (bg, palette[1]):
                    seen.add((dr, dc))
        for q in queries:
            required.update((dr, dc) for dr, dc, _, _ in seed_neighbours(q['input']))
    elif task_id == 'd511f180':
        a, b = palette[5], palette[8]
        for demo in demonstrations:
            if any((ink, demo['output'][r][c]) in ((a, b), (b, a))
                   for r, row in enumerate(demo['input']) for c, ink in enumerate(row)):
                seen.add('swap')
        if any(ink in (a, b) for q in queries for row in q['input'] for ink in row):
            required.add('swap')
    elif task_id == 'd631b094':
        if any(sum(c != bg for row in q['input'] for c in row) > 1 for q in queries):
            required.add('strip-axis')
        if any(sum(c != bg for row in d['input'] for c in row) > 1 for d in demonstrations):
            seen.add('strip-axis')
    elif task_id == 'd5d6de2d':
        def has_interior(g):
            pixels = {(r, c) for r, row in enumerate(g) for c, ink in enumerate(row) if ink != bg}
            while pixels:
                component = {pixels.pop()}
                stack = list(component)
                while stack:
                    r, c = stack.pop()
                    for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                        if p in pixels:
                            pixels.remove(p)
                            component.add(p)
                            stack.append(p)
                rows, cols = zip(*component)
                if max(rows)-min(rows) >= 2 and max(cols)-min(cols) >= 2:
                    return True
            return False
        if any(has_interior(q['input']) for q in queries):
            required.add('interior-fill')
        if any(palette[3] in row for d in demonstrations for row in d['output']):
            seen.add('interior-fill')
    elif task_id == 'd90796e8':
        def pairs(g):
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink != palette[3]:
                        continue
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        y, x = r+dr, c+dc
                        if 0 <= y < len(g) and 0 <= x < len(row) and g[y][x] == palette[2]:
                            yield r, c, y, x
        if any(any(pairs(q['input'])) for q in queries):
            required.add('touching-pair-recolour')
        if any(d['output'][r][c] == palette[8] and d['output'][y][x] == bg
               for d in demonstrations for r, c, y, x in pairs(d['input'])):
            seen.add('touching-pair-recolour')
    elif task_id == 'd037b0a7':
        def variants(g):
            h, w = len(g), len(g[0])
            results = []
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out = [row[:] for row in g]
                paths = ([(r, c) for r in range(h)[::dr]] for c in range(w)) if dr else (
                    [(r, c) for c in range(w)[::dc]] for r in range(h))
                for path in paths:
                    ink = bg
                    for r, c in path:
                        if g[r][c] != bg:
                            ink = g[r][c]
                        out[r][c] = ink
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'd23f8c26':
        def variants(g):
            h, w = len(g), len(g[0])
            return [[[ink if c == w//2 else bg for c, ink in enumerate(row)]
                     for row in g],
                    [[ink if r == h//2 else bg for ink in row]
                     for r, row in enumerate(g)]]
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'cf98881b':
        from itertools import permutations
        def variants(g):
            # Size-four panels separated by one full separator line. Candidate
            # precedence orders operate on the same visible panel coordinates.
            panels = ([[g[r][start:start+4] for r in range(4)]
                       for start in (0, 5, 10)] if len(g) == 4 else
                      [g[start:start+4] for start in (0, 5, 10)])
            return [[[next((panels[i][r][c] for i in order
                           if panels[i][r][c] != bg), bg)
                      for c in range(4)] for r in range(4)]
                    for order in permutations(range(3))]
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'd406998b':
        # Odd strip lengths give the same alternating mask from either end.
        # An even query needs an even-length demonstration to teach its anchor.
        if any(max(len(q['input']), len(q['input'][0])) % 2 == 0 for q in queries):
            required.add('even-strip-anchor')
        if any(max(len(d['input']), len(d['input'][0])) % 2 == 0
               for d in demonstrations):
            seen.add('even-strip-anchor')
    elif task_id == 'd2acf2cb':
        toggle = {palette[0]: palette[8], palette[8]: palette[0],
                  palette[6]: palette[7], palette[7]: palette[6]}
        def line_cells(g):
            h, w = len(g), len(g[0])
            return ({(r, c) for c in range(w)
                     if g[0][c] == g[-1][c] == palette[4] for r in range(1, h-1)}
                    | {(r, c) for r in range(h)
                       if g[r][0] == g[r][-1] == palette[4] for c in range(1, w-1)})
        for demo in demonstrations:
            for r, c in line_cells(demo['input']):
                src, dst = demo['input'][r][c], demo['output'][r][c]
                if toggle.get(src) == dst:
                    seen.add(tuple(sorted((src, dst))))
        for q in queries:
            for r, c in line_cells(q['input']):
                src = q['input'][r][c]
                if src in toggle:
                    required.add(tuple(sorted((src, toggle[src]))))
    elif task_id == 'c61be7dc':
        def even_axis(g):
            n = sum(c == palette[5] for row in g for c in row)
            if n == 0 or n % 2:
                return None
            rows = sum(all(c == palette[0] for c in row) for row in g)
            cols = sum(all(c == palette[0] for c in col) for col in zip(*g))
            return 'rows' if rows == 2 else 'cols' if cols == 2 else None
        for demo in demonstrations:
            axis = even_axis(demo['input'])
            if axis is not None:
                n = sum(c == palette[5] for row in demo['input'] for c in row)
                if sum(c == palette[5] for row in demo['output'] for c in row) == n:
                    seen.add(axis)
        required.update(axis for q in queries if (axis := even_axis(q['input'])) is not None)
    elif task_id == 'd0f5fe59':
        def multiple_objects(g):
            pixels = {(r, c) for r, row in enumerate(g) for c, ink in enumerate(row)
                      if ink != bg}
            if not pixels:
                return False
            stack = [pixels.pop()]
            while stack:
                r, c = stack.pop()
                for p in ((r+1, c), (r-1, c), (r, c+1), (r, c-1)):
                    if p in pixels:
                        pixels.remove(p)
                        stack.append(p)
            return bool(pixels)
        for demo in demonstrations:
            if multiple_objects(demo['input']) and len(demo['output']) > 1:
                seen.add('diagonal-axis')
        if any(multiple_objects(q['input']) for q in queries):
            required.add('diagonal-axis')
    elif task_id == 'c9e6f938':
        def variants(g):
            mirror_cols = [row[::-1] for row in g]
            mirror_rows = g[::-1]
            return [[a+b for a, b in zip(g, mirror_cols)],
                    [a+b for a, b in zip(mirror_cols, g)],
                    g+mirror_rows, mirror_rows+g]
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'cce03e0d':
        for demo in demonstrations:
            if (any(palette[2] in row for row in demo['input'])
                    and any(c != bg for row in demo['output'] for c in row)):
                seen.add('stamp-trigger')
        if any(palette[2] in row for q in queries for row in q['input']):
            required.add('stamp-trigger')
    elif task_id in ('c8f0f002', 'b1948b0a'):
        src, dst = ((palette[7], palette[5]) if task_id == 'c8f0f002'
                    else (palette[6], palette[2]))
        for demo in demonstrations:
            if any(ink == src and demo['output'][r][c] == dst
                   for r, row in enumerate(demo['input']) for c, ink in enumerate(row)):
                seen.add('substitution')
        if any(src in row for q in queries for row in q['input']):
            required.add('substitution')
    elif task_id == 'c1d99e64':
        def full_line(g):
            return (any(all(c == palette[0] for c in row) for row in g)
                    or any(all(c == palette[0] for c in col) for col in zip(*g)))
        for demo in demonstrations:
            if full_line(demo['input']) and any(palette[2] in row for row in demo['output']):
                seen.add('full-line-colour')
        if any(full_line(q['input']) for q in queries):
            required.add('full-line-colour')
    elif task_id == 'c8b7cc0f':
        def count_inside(g):
            points = [(r, c) for r, row in enumerate(g) for c, ink in enumerate(row)
                      if ink == palette[1]]
            if not points:
                return 0
            rows, cols = zip(*points)
            return sum(g[r][c] not in (bg, palette[1])
                       for r in range(min(rows)+1, max(rows))
                       for c in range(min(cols)+1, max(cols)))
        # Counts 3 and 6 show complete output lines, which cannot teach the
        # within-line fill direction. Asymmetric counts 4 or 5 teach both axes.
        for demo in demonstrations:
            n = count_inside(demo['input'])
            out = demo['output']
            if (n in (4, 5) and len(out) == 3 and all(len(row) == 3 for row in out)
                    and sum(c != bg for row in out for c in row) == n):
                seen.add('within-line-order')
        if any(count_inside(q['input']) in (4, 5) for q in queries):
            required.add('within-line-order')
    elif task_id == 'c0f76784':
        def frames(g):
            visited = set()
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink != palette[5] or (r, c) in visited:
                        continue
                    cells, stack = set(), [(r, c)]
                    visited.add((r, c))
                    while stack:
                        y, x = stack.pop()
                        cells.add((y, x))
                        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            p = y+dy, x+dx
                            if (0 <= p[0] < len(g) and 0 <= p[1] < len(row)
                                    and p not in visited and g[p[0]][p[1]] == palette[5]):
                                visited.add(p)
                                stack.append(p)
                    y0, y1 = min(y for y, x in cells), max(y for y, x in cells)
                    x0, x1 = min(x for y, x in cells), max(x for y, x in cells)
                    side = y1-y0+1
                    if side not in (3, 4, 5) or x1-x0+1 != side:
                        continue
                    border = {(y, x) for y in range(y0, y1+1)
                              for x in range(x0, x1+1)
                              if y in (y0, y1) or x in (x0, x1)}
                    if cells == border:
                        yield side, [(y, x) for y in range(y0+1, y1)
                                     for x in range(x0+1, x1)]
        for demo in demonstrations:
            for side, interior in frames(demo['input']):
                if all(demo['input'][r][c] == bg and
                       demo['output'][r][c] == palette[side+3] for r, c in interior):
                    seen.add(side)
        for query in queries:
            required.update(side for side, _ in frames(query['input']))
    elif task_id == 'bcb3040b':
        def crossings(g):
            markers = [(r, c) for r, row in enumerate(g) for c, ink in enumerate(row)
                       if ink == palette[2]]
            if len(markers) != 2:
                return []
            (r0, c0), (r1, c1) = markers
            dr, dc = r1-r0, c1-c0
            if dr and dc and abs(dr) != abs(dc):
                return []
            n = max(abs(dr), abs(dc))
            sy, sx = (dr > 0)-(dr < 0), (dc > 0)-(dc < 0)
            return [(r0+k*sy, c0+k*sx) for k in range(1, n)
                    if g[r0+k*sy][c0+k*sx] == palette[1]]
        for demo in demonstrations:
            if any(demo['output'][r][c] == palette[3]
                   for r, c in crossings(demo['input'])):
                seen.add('crossing-colour')
        if any(crossings(q['input']) for q in queries):
            required.add('crossing-colour')
    elif task_id == '6ea4a07e':
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
    elif task_id in ('a68b268e', 'e99362f0'):
        # The four panels share a coordinate system. A demonstrated overlap
        # establishes winner > loser; transitive precedence is also evidence.
        edges = set()
        def overlays(g):
            h, w = len(g)//2, len(g[0])//2
            for r in range(h):
                for c in range(w):
                    yield r, c, {g[y+r][x+c] for y in (0, h+1) for x in (0, w+1)} - {bg}
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
