"""Distinguish symmetry axes, periodic shifts and independent band phases."""
from .colour_evidence import MissingColourEvidence, _require_rule_agreement


def _period(values):
    return next(p for p in range(1, len(values)+1)
                if all(values[i] == values[i+p] for i in range(len(values)-p)))


def shift_variants(g):
    h, w = len(g), len(g[0])
    row_colours = {row[0] for row in g if len(set(row)) == 1}
    col_colours = {col[0] for col in zip(*g) if len(set(col)) == 1}
    frame = row_colours & col_colours
    if len(frame) != 1: raise MissingColourEvidence('caa06a1f: frame not uniquely visible')
    ink = next(iter(frame))
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != ink]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    tile = [row[c0:c1+1] for row in g[r0:r1+1]]
    py, px = _period(tile), _period(list(zip(*tile)))
    return [[[tile[(r+dy-r0)%py][(c+dx-c0)%px] for c in range(w)] for r in range(h)]
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))]


def band_variants(g, bg):
    n = len(g)
    main = all(g[i][i] != bg for i in range(n))
    anti = all(g[i][n-1-i] != bg for i in range(n))
    if main == anti: raise MissingColourEvidence('cad67732: band axis not unique')
    diag = [g[i][i if main else n-1-i] for i in range(n)]
    off = [g[i][i+1 if main else n-2-i] for i in range(n-1)]
    periods = [p for p in range(1, n) if all(diag[i] == diag[i+p] for i in range(n-p))
               and all(off[i] == off[i+p] for i in range(n-1-p))]
    if not periods: raise MissingColourEvidence('cad67732: no visible repeated band period')
    p = periods[0]
    predictions = []
    for bottom in (False, True):
        out = [[bg]*(2*n) for _ in range(2*n)]
        phase = -n if bottom else 0
        for r in range(2*n):
            c = r if main else 2*n-1-r
            out[r][c] = diag[(r+phase)%p]
            if r+1 < 2*n:
                nc = r+1 if main else 2*n-2-r
                out[r][nc] = out[r+1][c] = off[(r+phase)%p]
        predictions.append(out)
    # Main and anti phase choices are independent; a main-axis demonstration
    # cannot determine which end anchors a phase-sensitive anti-axis query.
    return [predictions[(bits >> (0 if main else 1)) & 1] for bits in range(4)]


def require_pattern_evidence(task_id, demonstrations, queries, palette):
    if task_id == 'caa06a1f':
        _require_rule_agreement(task_id, demonstrations, queries, shift_variants)
    elif task_id == 'cad67732':
        _require_rule_agreement(task_id, demonstrations, queries,
                                lambda g: band_variants(g, palette[0]))
    elif task_id == 'd56f2372':
        bg = palette[0]
        def predict(g, axis):
            candidates = []
            for ink in {v for row in g for v in row} - {bg}:
                cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == ink]
                r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
                c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
                crop = [[v if v == ink else bg for v in row[c0:c1+1]] for row in g[r0:r1+1]]
                mirror = crop[::-1] if axis == 0 else [row[::-1] for row in crop]
                if crop == mirror: candidates.append(crop)
            return candidates[0] if len(candidates) == 1 else None
        answers = []
        for axis in (0, 1):
            if not all(predict(d['input'], axis) == d['output'] for d in demonstrations): continue
            results = [predict(q['input'], axis) for q in queries]
            if any(out is None for out in results): continue
            answers.append(tuple(tuple(tuple(row) for row in out) for out in results))
        if not answers or len(set(answers)) != 1:
            raise MissingColourEvidence('d56f2372: demonstrations leave symmetric-selection axis ambiguous')
    else:
        raise ValueError('Unknown pattern family '+task_id)
