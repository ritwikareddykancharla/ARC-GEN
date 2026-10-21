"""Independent identifiability gate for 85fa5666 (corner rotation + diagonal rays).

Portable copy of ROOT/85fa5666/gate_85fa5666.py (pure Python, no factory code)
with the project's evidence signature.  Background, box colour and rotation
chirality are inferred from pixels, so palette/d4 may be omitted.  Uses
demonstration pairs and query INPUTS only; query labels are never read.

Readings: chirality x obstacle (pass/stop) x join (none/join/graze).  The native
random path is (pass, none).  Canonical train pair 2 needs join or graze.  A
query is accepted only if every reading that reproduces all demonstrations
renders the same full query grid.  Every non-continuation reading is refuted
by any native demonstration that shows the geometry where it differs, so
within the native domain a rejection means missing context, not intrinsic
ambiguity.  Callers should keep the query and resample demonstrations.
"""
from collections import Counter
from .colour_evidence import MissingColourEvidence

DIRS = {'TL': (-1, -1), 'TR': (-1, 1), 'BR': (1, 1), 'BL': (1, -1)}
NEXT_CW = {'TL': 'TR', 'TR': 'BR', 'BR': 'BL', 'BL': 'TL'}
NEXT_CCW = {v: k for k, v in NEXT_CW.items()}
READINGS = [(cw, ob, jn) for cw in (True, False) for ob in (False, True) for jn in ('none', 'join', 'graze')]


def roles(grids):
    cnt = Counter(v for g in grids for row in g for v in row)
    bg = cnt.most_common(1)[0][0]
    cands = []
    for col in cnt:
        if col == bg:
            continue
        ok = True
        for g in grids:
            cells = {(y, x) for y, row in enumerate(g) for x, v in enumerate(row) if v == col}
            while cells and ok:
                y, x = min(cells)
                sq = {(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)}
                if not sq <= cells:
                    ok = False
                cells -= sq
        if ok:
            cands.append(col)
    return bg, cands


def squares(g, box):
    H, W = len(g), len(g[0])
    cells = {(y, x) for y in range(H) for x in range(W) if g[y][x] == box}
    out = []
    for (y, x) in sorted(cells):
        sq = {(y, x), (y, x + 1), (y + 1, x), (y + 1, x + 1)}
        if sq <= cells:
            ring = {(y + a, x + b) for a in (-1, 0, 1, 2) for b in (-1, 0, 1, 2)
                    if (a in (0, 1)) != (b in (0, 1))}
            if not (ring & cells):
                out.append((y, x))
    return out, cells


def paint(g, bg, box, reading):
    cw, obstacle, join = reading
    H, W = len(g), len(g[0])
    ok = lambda y, x: 0 <= y < H and 0 <= x < W
    tops, boxcells = squares(g, box)
    corners = []  # (pos, direction, new colour)
    for (y, x) in tops:
        at = {'TL': (y - 1, x - 1), 'TR': (y - 1, x + 2), 'BR': (y + 2, x + 2), 'BL': (y + 2, x - 1)}
        giver = NEXT_CCW if cw else NEXT_CW  # cw: colour arrives from counter-clockwise neighbour
        for k, p in at.items():
            s = at[giver[k]]
            if ok(*p) and ok(*s) and g[s[0]][s[1]] not in (bg, box):
                corners.append((p, DIRS[k], g[s[0]][s[1]]))
    live = {}
    for (p, d, c) in corners:
        f = (p[0] + d[0], p[1] + d[1])
        if ok(*f) and g[f[0]][f[1]] == bg:
            live[p] = c
    out = [row[:] for row in g]
    for (p, d, c) in corners:
        y, x = p
        for _ in range(H + W):
            y, x = y + d[0], x + d[1]
            if not ok(y, x) or (y, x) in boxcells:
                break
            if g[y][x] != bg:
                if obstacle:
                    break
                continue
            out[y][x] = c
            if join != 'none':
                hit = any(live.get(n) == c for n in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)) if n != p)
                if hit and join == 'graze':
                    hit = (y + d[0], x) in boxcells or (y, x + d[1]) in boxcells
                if hit:
                    break
    for (p, d, c) in corners:
        out[p[0]][p[1]] = c
    return out


def assess(demos, query):
    grids = [d['input'] for d in demos] + [query]
    bg, cands = roles(grids)
    if len(cands) != 1:
        return {'status': 'roles_unidentified', 'candidates': cands}
    box = cands[0]
    surv = [r for r in READINGS
            if all(paint(d['input'], bg, box, r) == d['output'] for d in demos)]
    if not surv:
        return {'status': 'no_survivor'}
    outs = {}
    for r in surv:
        outs.setdefault(repr(paint(query, bg, box, r)), []).append(r)
    status = 'identified' if len(outs) == 1 else 'ambiguous'
    return {'status': status, 'bg': bg, 'box': box, 'survivors': surv, 'answer_classes': len(outs)}


def require_corner_rays_evidence(demonstrations, queries, palette=None, d4=0):
    """Raise MissingColourEvidence unless the demos identify every query output."""
    if not demonstrations or not queries:
        raise MissingColourEvidence('85fa5666: demonstrations and queries required')
    for q in queries:
        a = assess(demonstrations, q['input'])
        if a['status'] != 'identified':
            raise MissingColourEvidence('85fa5666: ' + a['status'] + ' ' + repr(a.get('survivors', a.get('candidates'))))
