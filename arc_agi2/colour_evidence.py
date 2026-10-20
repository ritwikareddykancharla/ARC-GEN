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
    if task_id == '891232d6':
        from .obstacle_path_evidence import require_obstacle_path_evidence
        require_obstacle_path_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == '3345333e':
        from .occluded_symmetry_evidence import require_occluded_symmetry_evidence
        require_occluded_symmetry_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == '6cf79266':
        from .hole_window_evidence import require_window_evidence
        require_window_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == '4852f2fa':
        from .repeated_crop_evidence import require_repeated_crop_evidence
        require_repeated_crop_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == 'abbfd121':
        from .wallpaper_evidence import require_wallpaper_evidence
        require_wallpaper_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == '94be5b80':
        from .legend_stack_evidence import require_legend_stack_evidence
        require_legend_stack_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == '93b4f4b3':
        from .gallery_alignment_evidence import require_gallery_evidence
        require_gallery_evidence(demonstrations, queries,
                    list(range(10)) if palette is None else palette)
        return
    if task_id == 'd9fac9be':
        from .framed_centre_evidence import require_framed_centre_evidence
        require_framed_centre_evidence(demonstrations, queries,
                                      list(range(10)) if palette is None else palette)
        return
    if task_id == '3a301edc':
        from .frame_band_evidence import require_band_evidence
        require_band_evidence(demonstrations, queries,
                              list(range(10)) if palette is None else palette)
        return
    if task_id == '72ca375d':
        from .object_symmetry_evidence import require_symmetry_evidence
        require_symmetry_evidence(demonstrations, queries,
                                  list(range(10)) if palette is None else palette)
        return
    if task_id == 'afe3afe9':
        from .lattice_pack_evidence import require_pack_evidence
        require_pack_evidence(demonstrations, queries,
                              list(range(10)) if palette is None else palette)
        return
    if task_id == '5168d44c':
        from .frame_motion_evidence import require_frame_motion_evidence
        require_frame_motion_evidence(demonstrations, queries,
                                      list(range(10)) if palette is None else palette)
        return
    if task_id == 'aa300dc3':
        from .diagonal_evidence import require_diagonal_evidence
        require_diagonal_evidence(demonstrations, queries,
                                  list(range(10)) if palette is None else palette)
        return
    if task_id == 'a1aa0c1e':
        from .ladder_evidence import require_ladder_evidence
        require_ladder_evidence(demonstrations, queries,
                                list(range(10)) if palette is None else palette, d4)
        return
    if task_id == 'a680ac02':
        from .frame_spacing_evidence import require_spacing_evidence
        require_spacing_evidence(demonstrations, queries,
                                 list(range(10)) if palette is None else palette)
        return
    if task_id == '7b7f7511':
        from .repeat_tile_context import require_repeat_evidence
        require_repeat_evidence(demonstrations, queries)
        return
    if task_id == 'c35c1b4c':
        from .central_mirror_evidence import require_central_mirror_evidence
        require_central_mirror_evidence(demonstrations, queries)
        return
    if task_id == '98c475bf':
        from .line_motif_evidence import require_line_motif_evidence
        require_line_motif_evidence(demonstrations, queries,
                                   list(range(10)) if palette is None else palette)
        return
    if task_id == 'e5c44e8f':
        from .spiral_evidence import require_spiral_evidence
        require_spiral_evidence(demonstrations, queries,
                               list(range(10)) if palette is None else palette)
        return
    if task_id == 'b7cb93ac':
        from .packing_evidence import require_packing_evidence
        require_packing_evidence(demonstrations, queries,
                                 list(range(10)) if palette is None else palette)
        return
    if task_id == '6df30ad6':
        from .nearest_marker_evidence import require_marker_evidence
        require_marker_evidence(demonstrations, queries,
                                list(range(10)) if palette is None else palette)
        return
    if task_id == 'd8e07eb2':
        from .catalogue_line_evidence import require_catalogue_evidence
        require_catalogue_evidence(demonstrations, queries,
                                   list(range(10)) if palette is None else palette)
        return
    if task_id == 'b0722778':
        from .analogy_priority_evidence import require_analogy_evidence
        require_analogy_evidence(demonstrations, queries,
                                list(range(10)) if palette is None else palette,d4)
        return
    if task_id == '7447852a':
        from .zigzag_evidence import require_zigzag_evidence
        require_zigzag_evidence(demonstrations, queries,
                                list(range(10)) if palette is None else palette)
        return
    if task_id == 'bd283c4a':
        from .count_sort_evidence import require_count_sort_evidence
        require_count_sort_evidence(demonstrations, queries)
        return
    if task_id == '9385bd28':
        from .paint_order_evidence import require_paint_evidence
        require_paint_evidence(demonstrations, queries,
                               list(range(10)) if palette is None else palette, d4)
        return
    if task_id == 'a32d8b75':
        from .legend_tile_evidence import require_tile_evidence
        require_tile_evidence(demonstrations, queries,
                              list(range(10)) if palette is None else palette, d4)
        return
    if task_id == '8e5c0c38':
        from .symmetry_selection_evidence import require_symmetry_selection_evidence
        require_symmetry_selection_evidence(demonstrations, queries)
        return
    if task_id in ('c87289bb', 'cc9053aa'):
        from .path_evidence import require_path_evidence
        require_path_evidence(task_id, demonstrations, queries,
                              list(range(10)) if palette is None else palette, d4)
        return
    if task_id in ('d56f2372', 'caa06a1f', 'cad67732'):
        from .pattern_evidence import require_pattern_evidence
        require_pattern_evidence(task_id, demonstrations, queries,
                                 list(range(10)) if palette is None else palette)
        return
    if task_id == 'dfadab01':
        from .motif_evidence import require_motif_evidence
        require_motif_evidence(demonstrations, queries,
                               list(range(10)) if palette is None else palette)
        return
    if task_id in ('ac605cbb', 'dc2e9a9d', 'db93a21d'):
        from .spatial_evidence import require_spatial_evidence
        require_spatial_evidence(task_id, demonstrations, queries,
                                 list(range(10)) if palette is None else palette, d4)
        return
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
                       'e760a62e', 'e8593010', 'e99362f0', 'ea9794b1', 'e6de6e8f',
                       'ed74f2f2', 'f2829549', 'ef135b50', 'f0afb749',
                       'f1bcbc2c', 'f5b8619d', 'f3e62deb',
                       'fafffa47', 'fd02da9e', 'fe9372f3', 'f9d67f8b',
                       'fea12743', 'ff28f65a', 'eee78d87', 'f28a3cbb', 'f8be4b64',
                       '37d3e8b2', 'ba9d41b8', 'd2abd087', 'e39e9282',
                       'b0c4d837', 'e133d23d', 'b27ca6d3', 'd94c3b52',
                       'ae3edfdc', 'e509e548', 'e5790162', 'e3721c99'):
        return
    palette = list(range(10)) if palette is None else palette
    bg = palette[0]
    colours = lambda g: {c for row in g for c in row} - {bg}
    required, seen = set(), set()
    if task_id == 'e3721c99':
        def unmatched(g):
            key_holes = set()
            for ink in {v for row in g for v in row} - {bg, palette[5]}:
                for cells in _colour_components(g, ink):
                    if any(r in (0, len(g)-1) or c in (0, len(g[0])-1) for r, c in cells):
                        continue  # border-touching divider, including L layouts
                    key_holes.add(_hole_count(cells))
            return [cells for cells in _colour_components(g, palette[5])
                    if _hole_count(cells) not in key_holes]
        if any(unmatched(q['input']) for q in queries): required.add('unmatched-blob-erasure')
        if any(any(all(d['output'][r][c] == bg for r, c in cells)
                   for cells in unmatched(d['input'])) for d in demonstrations):
            seen.add('unmatched-blob-erasure')
    elif task_id == 'ae3edfdc':
        for satellite, centre in ((palette[7], palette[1]), (palette[3], palette[2])):
            if any(satellite in row for q in queries for row in q['input']):
                required.add(satellite)
            for demo in demonstrations:
                a, b = demo['input'], demo['output']
                centres = [(r, c) for r, row in enumerate(a) for c, ink in enumerate(row) if ink == centre]
                if any(a[r][c] == satellite and b[r][c] != satellite
                       for r, row in enumerate(a) for c in range(len(row))):
                    if any(0 <= r+dy < len(b) and 0 <= c+dx < len(b[0])
                           and b[r+dy][c+dx] == satellite
                           for r, c in centres for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        seen.add(satellite)
    elif task_id == 'e509e548':
        def category(cells):
            branch, corners = False, 0
            for r, c in cells:
                horizontal = int((r, c-1) in cells) + int((r, c+1) in cells)
                vertical = int((r-1, c) in cells) + int((r+1, c) in cells)
                branch |= horizontal + vertical >= 3
                corners += horizontal == vertical == 1
            return 'H' if branch else 'U' if corners >= 2 else 'L'
        ink_for = {'H': palette[2], 'U': palette[6], 'L': palette[1]}
        for demo in demonstrations:
            for cells in _colour_components(demo['input'], palette[3]):
                key = category(cells)
                if all(demo['output'][r][c] == ink_for[key] for r, c in cells): seen.add(key)
        for query in queries:
            required.update(category(cells) for cells in _colour_components(query['input'], palette[3]))
    elif task_id == 'e5790162':
        def variants(g):
            starts = [(r, c) for r, row in enumerate(g) for c, ink in enumerate(row) if ink == palette[3]]
            if len(starts) != 1:
                raise MissingColourEvidence('e5790162: expected one snake start')
            h, w = len(g), len(g[0])
            y0, x0 = starts[0]
            headings = [(dy, dx) for edge, dy, dx in
                        ((y0 == 0, 1, 0), (y0 == h-1, -1, 0),
                         (x0 == 0, 0, 1), (x0 == w-1, 0, -1)) if edge]
            if len(headings) != 1:
                raise MissingColourEvidence('e5790162: start heading is ambiguous')
            outputs = []
            # Each obstacle independently means clockwise or counterclockwise.
            # Do not infer the second colour merely by assuming a bijection.
            for turns in range(4):
                out = [row[:] for row in g]
                y, x = y0, x0
                dy, dx = headings[0]
                visited = set()
                while True:
                    state = y, x, dy, dx
                    if state in visited:
                        out = [[-1]]  # Invalid cyclic hypothesis, never a target.
                        break
                    visited.add(state)
                    yy, xx = y+dy, x+dx
                    if not (0 <= yy < h and 0 <= xx < w): break
                    ink = g[yy][xx]
                    if ink in (palette[6], palette[8]):
                        bit = 0 if ink == palette[6] else 1
                        dy, dx = (dx, -dy) if turns & (1 << bit) else (-dx, dy)
                    else:
                        y, x = yy, xx
                        out[y][x] = palette[3]
                outputs.append(out)
            return outputs
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'b0c4d837':
        from .augmentation import transformed
        def empty_layers(g):
            cells = [(r, c) for r, row in enumerate(g)
                     for c, ink in enumerate(row) if ink == palette[5]]
            if not cells:
                raise MissingColourEvidence('b0c4d837: missing cup walls')
            r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
            c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
            segments = ([g[r][c0+1:c1] for r in range(r0, r1+1)]
                        if d4 % 2 == 0 else
                        [[g[r][c] for r in range(r0+1, r1)] for c in range(c0, c1+1)])
            return sum(bool(line) and all(ink == bg for ink in line) for line in segments)
        def variants(g):
            n = empty_layers(g)
            outputs = []
            # Up to the first row, snake and raster traversal coincide. Compare
            # both orders in every orientation on this query, not query labels.
            for snake in (False, True):
                order = [(r, c) for r in range(3)
                         for c in (range(2, -1, -1) if snake and r % 2 else range(3))]
                out = [[bg]*3 for _ in range(3)]
                for r, c in order[:n]: out[r][c] = palette[8]
                outputs.extend(transformed(out, orient, list(range(10))) for orient in range(8))
            return outputs
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'e133d23d':
        def marked(g):
            return any(ink in (palette[6], palette[8]) for row in g for ink in row)
        if any(marked(q['input']) for q in queries): required.add('union-paint')
        if any(marked(d['input']) and palette[2] in colours(d['output']) for d in demonstrations):
            seen.add('union-paint')
    elif task_id == 'b27ca6d3':
        def ring_cells(g):
            cells = set()
            for part in _colour_components(g, palette[2]):
                if len(part) != 2: continue
                r0, r1 = min(r for r, c in part), max(r for r, c in part)
                c0, c1 = min(c for r, c in part), max(c for r, c in part)
                cells.update((r, c) for r in range(max(0, r0-1), min(len(g), r1+2))
                             for c in range(max(0, c0-1), min(len(g[0]), c1+2)) if g[r][c] == bg)
            return cells
        if any(ring_cells(q['input']) for q in queries): required.add('domino-ring-paint')
        if any(any(d['output'][r][c] == palette[3] for r, c in ring_cells(d['input']))
               for d in demonstrations): seen.add('domino-ring-paint')
    elif task_id == 'd94c3b52':
        def between_cells(g):
            h, w = (len(g)-1)//4, (len(g[0])-1)//4
            masks = {(r, c): frozenset((y, x) for y in range(3) for x in range(3)
                                      if g[1+4*r+y][1+4*c+x] != bg)
                     for r in range(h) for c in range(w)}
            templates = [masks[r, c] for r in range(h) for c in range(w)
                         if any(g[1+4*r+y][1+4*c+x] == palette[8]
                                for y in range(3) for x in range(3))]
            if not templates: return set()
            matches = {p for p, mask in masks.items() if mask == templates[0]}
            fill = set()
            for r in range(h):
                xs = [c for y, c in matches if y == r]
                if len(xs) >= 2: fill.update((r, c) for c in range(min(xs)+1, max(xs)))
            for c in range(w):
                ys = [r for r, x in matches if x == c]
                if len(ys) >= 2: fill.update((r, c) for r in range(min(ys)+1, max(ys)))
            return {(1+4*r+y, 1+4*c+x) for r, c in fill-matches for y, x in masks[r, c]}
        if any(between_cells(q['input']) for q in queries): required.add('between-tiles-paint')
        if any(any(d['output'][r][c] == palette[7] for r, c in between_cells(d['input']))
               for d in demonstrations): seen.add('between-tiles-paint')
    elif task_id == 'f8be4b64':
        def variants(g):
            h, w = len(g), len(g[0])
            steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
            candidates = {}
            for r in range(1, h-1):
                for c in range(1, w-1):
                    arms = {(r+dr, c+dc) for dr, dc in steps}
                    if g[r][c] != palette[3] and all(g[y][x] == palette[3] for y, x in arms):
                        candidates[r, c] = arms
            centres = []
            for p, arms in candidates.items():
                others = set().union(*(a for q, a in candidates.items() if q != p))
                if g[p[0]][p[1]] != bg or arms - others:
                    centres.append(p)
            results = []
            for axes in (((0, 1), (1, 0)), ((1, 0), (0, 1))):
                out = [row[:] for row in g]
                for dr, dc in axes:
                    for r, c in centres:
                        for sign in (-1, 1):
                            y, x = r+2*sign*dr, c+2*sign*dc
                            while 0 <= y < h and 0 <= x < w and g[y][x] == bg:
                                out[y][x] = g[r][c]
                                y, x = y+sign*dr, x+sign*dc
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'f28a3cbb':
        def variants(g):
            background = palette[6]
            objects = []
            for ink in sorted({v for row in g for v in row} - {background}):
                components = list(_colour_components(g, ink))
                block = max(components, key=len)
                box = (min(r for r, c in block), max(r for r, c in block),
                       min(c for r, c in block), max(c for r, c in block))
                strays = set().union(*components) - block
                objects.append((ink, box, strays))
            results = []
            # Compare nearest-face clamping with the archived constant-direction
            # diagonal slide. Include all row/column tie orders for the slide.
            for mode in range(9):
                out = [row[:] for row in g]
                for ink, box, strays in objects:
                    for r, c in strays: out[r][c] = background
                for ink, (r0, r1, c0, c1), strays in objects:
                    def distance(p):
                        r, c = p
                        return max(r0-r, r-r1, c0-c, c-c1, 0)
                    direction = max(0, mode-1)
                    axis = direction // 4
                    s1, s2 = (-1 if direction & 2 else 1), (-1 if direction & 1 else 1)
                    ordered = sorted(strays, key=lambda p: (distance(p), s1*p[axis], s2*p[1-axis]))
                    for r, c in ordered:
                        dr = 1 if r < r0 else -1 if r > r1 else 0
                        dc = 1 if c < c0 else -1 if c > c1 else 0
                        if mode == 0:
                            oy, ox = max(r0-r, r-r1, 0), max(c0-c, c-c1, 0)
                            y = r0-1 if r < r0 else r1+1
                            x = c0-1 if c < c0 else c1+1
                            if oy > ox: x = min(max(c, c0), c1)
                            elif ox > oy: y = min(max(r, r0), r1)
                        else:
                            y, x = r, c
                            while dr or dc:
                                yy, xx = y+dr, x+dc
                                if not (0 <= yy < len(g) and 0 <= xx < len(g[0])) or out[yy][xx] == ink:
                                    break
                                y, x = yy, xx
                        out[y][x] = ink
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'eee78d87':
        def variants(g):
            cells = [(r, c) for r, row in enumerate(g)
                     for c, ink in enumerate(row) if ink != palette[7]]
            top = min(r for r, c in cells)
            left = min(c for r, c in cells)
            filled = lambda y, x: g[top+y][left+x] != palette[7]
            # The fixtures confound corner occupancy with a complemented
            # edge-midpoint bit. Require agreement on the same visible query,
            # or a demonstration that distinguishes these interpretations.
            results = []
            for corner in (filled(0, 0), not filled(0, 1), not filled(1, 0)):
                bits = {(True, True): filled(1, 1),
                        (True, False): filled(1, 0),
                        (False, True): filled(0, 1),
                        (False, False): corner}
                out = []
                for r in range(16):
                    row = []
                    for c in range(16):
                        ink = palette[0] if bits[r % 3 == 0, c % 3 == 0] else palette[7]
                        if ink == palette[0] and 5 <= r <= 10 and 5 <= c <= 10:
                            ink = palette[9]
                        row.append(ink)
                    out.append(row)
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'fea12743':
        from itertools import combinations
        def variants(g):
            tiles = {(r, c): {(y, x) for y in range(4) for x in range(4)
                              if g[1+5*r+y][1+5*c+x] != bg}
                     for r in range((len(g)-1)//5) for c in range((len(g[0])-1)//5)}
            maximum = max(tiles, key=lambda p: len(tiles[p]))
            mask = tiles[maximum]
            pairs = [(a, b) for a, b in combinations(tiles, 2)
                     if maximum not in (a, b) and tiles[a] | tiles[b] == mask]
            results = []
            for axis in (0, 1):
                for first in (-1, 1):
                    for second in (-1, 1):
                        order = sorted(tiles, key=lambda p: (first*p[axis], second*p[1-axis]))
                        ranks = {p: i for i, p in enumerate(order)}
                        selected = min(pairs, key=lambda ab: sorted(ranks[p] for p in ab))
                        out = [row[:] for row in g]
                        for p, ink in [(maximum, palette[3])]+[(p, palette[8]) for p in selected]:
                            for y, x in tiles[p]: out[1+5*p[0]+y][1+5*p[1]+x] = ink
                        results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'ff28f65a':
        from .augmentation import transformed
        order = [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)]
        def variants(g):
            count = sum(1 for _ in _colour_components(g, palette[2]))
            out = [[bg]*3 for _ in range(3)]
            for r, c in order[:count]: out[r][c] = palette[1]
            return [transformed(out, direction, list(range(10))) for direction in range(8)]
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'fd02da9e':
        canvas = palette[7]
        figures = {(0, 0): [(1, 1), (1, 2), (2, 1), (2, 2)],
                   (0, 7): [(1, 5), (1, 6), (2, 5), (2, 6)],
                   (7, 0): [(4, 2), (5, 2), (6, 3)],
                   (7, 7): [(4, 5), (5, 5), (6, 4)]}
        def move(y, x, direction):
            if direction >= 4:
                x = 7 - x
            for _ in range(direction % 4):
                y, x = x, 7 - y
            return y, x
        tables = [{move(*corner, direction): [move(*cell, direction) for cell in shape]
                   for corner, shape in figures.items()} for direction in range(8)]
        def variants(g):
            results = []
            for table in tables:
                out = [[canvas] * 8 for _ in range(8)]
                for (r, c), shape in table.items():
                    for y, x in shape:
                        out[y][x] = g[r][c]
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'fe9372f3':
        def has_mark(g):
            cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == palette[2]]
            y = (min(r for r, c in cells) + max(r for r, c in cells)) // 2
            x = (min(c for r, c in cells) + max(c for r, c in cells)) // 2
            return max(y, x, len(g)-1-y, len(g[0])-1-x) >= 4
        if any(has_mark(q['input']) for q in queries): required.add('periodic-marker-colour')
        if any(has_mark(d['input']) and palette[4] in colours(d['output']) for d in demonstrations):
            seen.add('periodic-marker-colour')
    elif task_id == 'f9d67f8b':
        # The first two native rows/columns lie outside the H/V mirror crop.
        # Track its off-centre axes in the visible orientation; only inputs
        # determine whether a diagonal-repair demonstration is needed.
        def needs_diagonal(g):
            h, w = len(g), len(g[0])
            ay, ax = (h+2)//2, (w+2)//2
            if d4 >= 4: ax = w-ax
            for _ in range(d4 % 4):
                ay, ax, h, w = ax, h-ay, w, h
            for r, row in enumerate(g):
                for c, ink in enumerate(row):
                    if ink != palette[9]: continue
                    partners = ((r, 2*ax-1-c), (2*ay-1-r, c), (2*ay-1-r, 2*ax-1-c))
                    if not any(0 <= y < h and 0 <= x < w and g[y][x] != palette[9]
                               for y, x in partners): return True
            return False
        if any(needs_diagonal(q['input']) for q in queries): required.add('diagonal-repair')
        if any(needs_diagonal(d['input']) and all(palette[9] not in row for row in d['output'])
               for d in demonstrations): seen.add('diagonal-repair')
    elif task_id == 'f1bcbc2c':
        wall, plug, paint = palette[7], palette[9], palette[8]
        def variants(g):
            h, w = len(g), len(g[0])
            borders = [([(0, c) for c in range(1, w-1)], (0, 1)),
                       ([(r, w-1) for r in range(1, h-1)], (1, 0)),
                       ([(h-1, c) for c in range(1, w-1)], (0, 1)),
                       ([(r, 0) for r in range(1, h-1)], (1, 0))]
            results = []
            for cells, (dy, dx) in borders:
                starts = [(r, c) for r, c in cells if g[r][c] == bg
                          and g[r-dy][c-dx] == g[r+dy][c+dx] == wall]
                out = [row[:] for row in g]
                if len(starts) != 1:
                    results.append(out)
                    continue
                current = starts[0]
                visited = {current}
                out[current[0]][current[1]] = paint
                while True:
                    r, c = current
                    following = [(r+dr, c+dc, dr, dc) for dr, dc in
                                 ((1, 0), (-1, 0), (0, 1), (0, -1))
                                 if 0 <= r+dr < h and 0 <= c+dc < w
                                 and (r+dr, c+dc) not in visited
                                 and g[r+dr][c+dc] in (bg, plug)]
                    if len(following) != 1:
                        break
                    y, x, dr, dc = following[0]
                    if g[y][x] == plug and not (
                            0 <= y+dr < h and 0 <= x+dc < w and g[y+dr][x+dc] == bg):
                        break
                    out[y][x] = paint
                    current = (y, x)
                    visited.add(current)
                results.append(out)
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'f5b8619d':
        # A symmetric demo can conceal the line axis. A full coloured line can
        # conceal the new fill colour. Compare both axes and all ten colours.
        def variants(g):
            h, w = len(g), len(g[0])
            tile = [[g[r % h][c % w] for c in range(2*w)] for r in range(2*h)]
            results = []
            for axis in (0, 1):
                occupied = {c if axis == 0 else r
                            for r, row in enumerate(tile) for c, v in enumerate(row) if v != bg}
                for fill in range(10):
                    results.append([[fill if v == bg and (c if axis == 0 else r) in occupied else v
                                     for c, v in enumerate(row)] for r, row in enumerate(tile)])
            return results
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == 'f3e62deb':
        roles = {palette[c] for c in (3, 4, 6, 8)}
        for demo in demonstrations:
            for ink in colours(demo['input']) & roles:
                before = [(r, c) for r, row in enumerate(demo['input']) for c, v in enumerate(row) if v == ink]
                after = [(r, c) for r, row in enumerate(demo['output']) for c, v in enumerate(row) if v == ink]
                if len(before) == len(after) and before and before != after:
                    shifts = {(y-r, x-c) for (r, c), (y, x) in zip(before, after)}
                    if len(shifts) == 1:
                        dr, dc = next(iter(shifts))
                        if (dr == 0) != (dc == 0):
                            seen.add(ink)
        for query in queries:
            required.update(colours(query['input']) & roles)
    elif task_id == 'd2abd087':
        # Both branches have arbitrary paint colours; observe a corresponding
        # demonstration before asking for that branch on the query.
        for demo in demonstrations:
            for cells in _colour_components(demo['input'], palette[5]):
                branch = len(cells) == 6
                ink = palette[2] if branch else palette[1]
                if all(demo['output'][r][c] == ink for r, c in cells):
                    seen.add(branch)
        for query in queries:
            required.update(len(cells) == 6 for cells in
                            _colour_components(query['input'], palette[5]))
    elif task_id == 'e39e9282':
        # Every generated block has at least one marker and undergoes its
        # colour-specific action, making a demonstrated block informative.
        roles = {palette[5], palette[6]}
        for demo in demonstrations:
            seen.update(v for row in demo['input'] for v in row if v in roles)
        for query in queries:
            required.update(v for row in query['input'] for v in row if v in roles)
    elif task_id == 'ba9d41b8':
        def variants(g):
            boxes = []
            for colour in {v for row in g for v in row} - {bg}:
                for cells in _colour_components(g, colour):
                    boxes.append((min(r for r, c in cells), max(r for r, c in cells),
                                  min(c for r, c in cells), max(c for r, c in cells)))
            outputs = []
            for bottom, right in ((False, False), (False, True),
                                  (True, True), (True, False)):
                out = [row[:] for row in g]
                for y0, y1, x0, x1 in boxes:
                    ay, ax = (y1 if bottom else y0), (x1 if right else x0)
                    for y in range(y0+1, y1):
                        for x in range(x0+1, x1):
                            if (y-ay+x-ax) % 2 == 0:
                                out[y][x] = bg
                outputs.append(out)
            return outputs
        _require_rule_agreement(task_id, demonstrations, queries, variants)
        return
    elif task_id == '37d3e8b2':
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
    elif task_id == 'ed74f2f2':
        from .augmentation import transformed
        mask = transformed([[int(1 <= r <= 3 and 1 <= c <= 3)
                             for c in range(9)] for r in range(5)],
                           d4, list(range(10)))
        positions = [(r, c) for r, row in enumerate(mask) for c, v in enumerate(row) if v]
        def glyph(g):
            return tuple(g[r][c] != bg for r, c in positions)
        for demo in demonstrations:
            if len(colours(demo['output'])) == 1:
                seen.add(glyph(demo['input']))
        required.update(glyph(q['input']) for q in queries)
    elif task_id in ('e345f17b', 'f2829549', 'fafffa47'):
        gap, mark = {'e345f17b': (0, palette[4]), 'f2829549': (1, palette[3]),
                     'fafffa47': (0, palette[2])}[task_id]
        vertical = bool(d4 % 2) != (task_id == 'fafffa47')
        def has_nor(g):
            if vertical:
                half = len(g)//2
                return any(a == b == bg for x, y in zip(g[:half], g[half+gap:])
                           for a, b in zip(x, y))
            half = len(g[0])//2
            return any(row[c] == row[c+half+gap] == bg for row in g for c in range(half))
        if any(has_nor(q['input']) for q in queries):
            required.add('nor-mark-colour')
        if any(has_nor(d['input']) and any(mark in row for row in d['output'])
               for d in demonstrations):
            seen.add('nor-mark-colour')
    elif task_id == 'ef135b50':
        red, fill = palette[2], palette[9]
        def has_gap(g):
            a = list(zip(*g)) if d4 % 2 else g
            for r, row in enumerate(a):
                reds = [c for c, v in enumerate(row) if v == red]
                for left, right in zip(reds, reds[1:]):
                    if right <= left + 1: continue
                    if all(row[c] == bg and (r == 0 or a[r-1][c] != red)
                           and (r == len(a)-1 or a[r+1][c] != red)
                           for c in range(left+1, right)):
                        return True
            return False
        if any(has_gap(q['input']) for q in queries): required.add('gap-fill-colour')
        if any(has_gap(d['input']) and fill in colours(d['output']) for d in demonstrations):
            seen.add('gap-fill-colour')
    elif task_id == 'f0afb749':
        anti = (d4 % 4 + int(d4 >= 4)) % 2
        def has_ray(g):
            h, w = 2 * len(g), 2 * len(g[0])
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == bg: continue
                    starts = ((2*r+2, 2*c-1), (2*r-1, 2*c+2)) if anti else (
                        (2*r+2, 2*c+2), (2*r-1, 2*c-1))
                    if any(0 <= y < h and 0 <= x < w for y, x in starts): return True
            return False
        if any(has_ray(q['input']) for q in queries): required.add('ray-colour')
        if any(has_ray(d['input']) and palette[1] in colours(d['output']) for d in demonstrations):
            seen.add('ray-colour')
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
    elif task_id in ('a68b268e', 'e99362f0', 'ea9794b1'):
        # The four panels share a coordinate system. A demonstrated overlap
        # establishes winner > loser; transitive precedence is also evidence.
        edges = set()
        def overlays(g):
            h, w = len(g)//2, len(g[0])//2
            gap = 0 if task_id == 'ea9794b1' else 1
            for r in range(h):
                for c in range(w):
                    yield r, c, {g[y+r][x+c] for y in (0, h+gap) for x in (0, w+gap)} - {bg}
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
