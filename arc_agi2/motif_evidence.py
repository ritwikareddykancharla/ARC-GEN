"""Check visible 4x4 motif evidence without reading query answers or motif tables."""
from .colour_evidence import MissingColourEvidence


class _Conflict(ValueError):
    pass


def _analyse(g, bg, marker_colours, anchor):
    h, w = len(g), len(g[0])
    remaining = {(r, c) for r, row in enumerate(g) for c, ink in enumerate(row) if ink != bg}
    ignored, legends = set(), []
    ay, ax = anchor
    ky_sign, kx_sign = (1 if ay == 0 else -1), (1 if ax == 0 else -1)
    while remaining:
        start = remaining.pop()
        ink = g[start[0]][start[1]]
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    p = r+dy, c+dx
                    if p in remaining and g[p[0]][p[1]] == ink:
                        remaining.remove(p); cells.add(p); stack.append(p)
        if len(cells) == 1: continue
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        if r1-r0 != 3 or c1-c0 != 3:
            raise _Conflict('legend must occupy a full 4x4 box')
        kr = (r1 if ky_sign > 0 else r0)+ky_sign
        kc = (c1 if kx_sign > 0 else c0)+kx_sign
        if not (0 <= kr < h and 0 <= kc < w and g[kr][kc] in marker_colours):
            raise _Conflict('legend key contradicts anchor')
        key = g[kr][kc]
        legends.append((key, {(r, c): ink if (r0+r, c0+c) in cells else bg
                              for r in range(4) for c in range(4)}))
        ignored.update(cells); ignored.add((kr, kc))
    markers = [(r, c, ink) for r, row in enumerate(g) for c, ink in enumerate(row)
               if ink != bg and (r, c) not in ignored]
    if any(ink not in marker_colours for r, c, ink in markers):
        raise _Conflict('unexplained non-marker pixels')
    return legends, markers


def require_motif_evidence(demonstrations, queries, palette):
    bg, marker_colours = palette[0], {palette[k] for k in (2, 3, 5, 8)}
    candidates, incomplete = [], False
    for anchor in ((0, 0), (0, 3), (3, 0), (3, 3)):
        try:
            observations = {}
            def note(key, cell, ink):
                entries = observations.setdefault(key, {})
                if cell in entries and entries[cell] != ink:
                    raise _Conflict('inconsistent motif observations')
                entries[cell] = ink
            demos = [(_analyse(d['input'], bg, marker_colours, anchor), d) for d in demonstrations]
            query_parts = [_analyse(q['input'], bg, marker_colours, anchor) for q in queries]
            for (legends, _), _demo in demos:
                for key, cells in legends:
                    for cell, ink in cells.items(): note(key, cell, ink)
            for legends, _ in query_parts:
                for key, cells in legends:
                    for cell, ink in cells.items(): note(key, cell, ink)
            ay, ax = anchor
            for (_, markers), demo in demos:
                out = demo['output']; h, w = len(out), len(out[0])
                if h != len(demo['input']) or w != len(demo['input'][0]):
                    raise _Conflict('stamp output shape changed')
                covered = set()
                for r, c, key in markers:
                    for y in range(4):
                        for x in range(4):
                            yy, xx = r-ay+y, c-ax+x
                            if 0 <= yy < h and 0 <= xx < w:
                                if (yy, xx) in covered: raise _Conflict('stamp boxes overlap')
                                covered.add((yy, xx)); note(key, (y, x), out[yy][xx])
                if any(ink != bg and (r, c) not in covered
                       for r, row in enumerate(out) for c, ink in enumerate(row)):
                    raise _Conflict('demonstrated paint lies outside anchored stamp boxes')
            predictions, unknown = [], False
            for query, (_, markers) in zip(queries, query_parts):
                h, w = len(query['input']), len(query['input'][0])
                out = [[bg]*w for _ in range(h)]
                for r, c, key in markers:
                    for y in range(4):
                        for x in range(4):
                            yy, xx = r-ay+y, c-ax+x
                            if 0 <= yy < h and 0 <= xx < w:
                                if (y, x) not in observations.get(key, {}): unknown = True
                                else: out[yy][xx] = observations[key][y, x]
                predictions.append(tuple(tuple(row) for row in out))
            if unknown: incomplete = True
            else: candidates.append(tuple(predictions))
        except _Conflict:
            continue
    if incomplete or not candidates or len(set(candidates)) != 1:
        raise MissingColourEvidence('dfadab01: motif cells, paint colour or anchor not determined by visible evidence')
