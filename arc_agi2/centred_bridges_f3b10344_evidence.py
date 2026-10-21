"""Independent episode-evidence gate for f3b10344 (same-colour rectangle bridges).

This file is implemented separately from the emitted program. It uses NumPy,
finds rectangles with a raster corner scan instead of flood fill, works on
projection intervals, and infers background and bridge colours only from the
demonstrations, so the palette is never used for inference. It reads
demonstration pairs and query INPUTS only, never query outputs.

A rival rule is (alignment, blocker):
  alignment: 'centred' (equal centre on the shared axis, constructor) or
             'overlap' (any positive shared span)
  blocker:   'trim_any' | 'trim_same' | 'span_any' | 'span_same' | 'none'
A bridge is gap x (shared span minus one cell per end). It is painted on
background cells only.

assess(demonstrations, queries) -> dict with status
  identified        all demo-consistent rules agree on every query
  context_shortfall rules fit every demo but disagree on some query (keep the
                    query, resample the demos)
  colour_shortfall  a query needs a bridge but no demo shows the bridge colour
  no_survivor       no rival rule reproduces the demos
  out_of_domain     objects are not separated solid rectangles
require_centred_bridge_evidence(demonstrations, queries, palette=None) raises
MissingColourEvidence unless the status is 'identified'.
"""
from collections import Counter
import numpy as np
from .colour_evidence import MissingColourEvidence

ALIGN = ('centred', 'overlap')
BLOCK = ('trim_any', 'trim_same', 'span_any', 'span_same', 'none')
RULES = tuple((a, b) for a in ALIGN for b in BLOCK)


def _arr(g):
    return np.asarray(g, dtype=int)


def infer_colours(demonstrations):
    bg = Counter()
    changed = set()
    for d in demonstrations:
        a, b = _arr(d['input']), _arr(d['output'])
        bg.update(a.ravel().tolist())
        if a.shape != b.shape:
            return None, 'mixed'
        diff = a != b
        if diff.any():  # whether changed cells were background is judged by rule fitting
            changed |= set(np.unique(b[diff]).tolist())
    background = bg.most_common(1)[0][0] if bg else None
    if len(changed) > 1:
        return background, 'mixed'
    return background, (changed.pop() if changed else None)


def rectangles(a, bg):
    H, W = a.shape
    taken = np.zeros(a.shape, dtype=bool)
    found = []
    for y in range(H):
        for x in range(W):
            if a[y, x] == bg or taken[y, x]:
                continue
            c = a[y, x]
            x1 = x
            while x1 + 1 < W and a[y, x1 + 1] == c:
                x1 += 1
            y1 = y
            while y1 + 1 < H and a[y1 + 1, x] == c:
                y1 += 1
            if not (a[y:y1 + 1, x:x1 + 1] == c).all():
                return None
            taken[y:y1 + 1, x:x1 + 1] = True
            found.append((int(c), y, y1, x, x1))
    for c, y0, y1, x0, x1 in found:
        # maximal component: the one-cell ring holds no further cell of colour c
        ring = a[max(0, y0 - 1):y1 + 2, max(0, x0 - 1):x1 + 2]
        if int((ring == c).sum()) != (y1 - y0 + 1) * (x1 - x0 + 1):
            return None
    return found


def _links(found):
    """(colour, centred, bridge slices, span slices) for every facing same-colour pair."""
    links = []
    for i, (c, ay0, ay1, ax0, ax1) in enumerate(found):
        for d, by0, by1, bx0, bx1 in found[i + 1:]:
            if c != d:
                continue
            for (p0, p1, q0, q1), (r0, r1, s0, s1), axis in (
                    ((ay0, ay1, ax0, ax1), (by0, by1, bx0, bx1), 0),
                    ((ax0, ax1, ay0, ay1), (bx0, bx1, by0, by1), 1)):
                lo, hi = max(p0, r0), min(p1, r1)          # shared span on this axis
                if lo > hi:
                    continue
                g0, g1 = min(q1, s1) + 1, max(q0, s0) - 1  # gap on the other axis
                if g0 > g1:
                    continue
                centred = p0 + p1 == r0 + r1
                if axis == 0:
                    bridge = (slice(lo + 1, hi), slice(g0, g1 + 1))
                    span = (slice(lo, hi + 1), slice(g0, g1 + 1))
                else:
                    bridge = (slice(g0, g1 + 1), slice(lo + 1, hi))
                    span = (slice(g0, g1 + 1), slice(lo, hi + 1))
                links.append((c, centred, bridge, span))
    return links


def predict(a, bg, br, rule):
    found = rectangles(a, bg)
    if found is None:
        return None
    align, block = rule
    paint = np.zeros(a.shape, dtype=bool)
    for c, centred, bridge, span in _links(found):
        if align == 'centred' and not centred:
            continue
        if a[bridge].size == 0:
            continue
        if block == 'trim_any':
            ok = bool((a[bridge] == bg).all())
        elif block == 'trim_same':
            ok = not bool((a[bridge] == c).any())
        elif block == 'span_any':
            ok = bool((a[span] == bg).all())
        elif block == 'span_same':
            ok = not bool((a[span] == c).any())
        else:
            ok = True
        if ok:
            paint[bridge] = True
    out = a.copy()
    out[paint & (a == bg)] = -1 if br is None else br
    return out


def assess(demonstrations, queries):
    demos = list(demonstrations)
    if not demos:
        return {'status': 'no_survivor', 'reason': 'no demonstrations'}
    bg, br = infer_colours(demos)
    if bg is None or br == 'mixed':
        return {'status': 'no_survivor', 'reason': 'demos do not show one background and one bridge colour'}
    fits = {}
    for rule in RULES:
        ok = True
        for d in demos:
            a, b = _arr(d['input']), _arr(d['output'])
            if br is not None and (a == br).any():
                return {'status': 'out_of_domain', 'reason': 'bridge colour in a demo input'}
            p = predict(a, bg, br, rule)
            if p is None:
                return {'status': 'out_of_domain', 'reason': 'demo objects are not separated solid rectangles'}
            ok = ok and p.shape == b.shape and bool((p == b).all())
        fits[rule] = ok
    survivors = [r for r in RULES if fits[r]]
    if not survivors:
        return {'status': 'no_survivor', 'fits': {'/'.join(k): v for k, v in fits.items()}}
    result = {'status': 'identified', 'background': int(bg), 'bridge': None if br is None else int(br),
              'survivors': ['/'.join(r) for r in survivors], 'query_discriminates': []}
    for k, query in enumerate(queries):
        q = _arr(query['input'])
        if br is not None and (q == br).any():
            return {'status': 'out_of_domain', 'reason': 'bridge colour in a query input'}
        preds = {}
        for rule in RULES:
            p = predict(q, bg, br, rule)
            if p is None:
                return {'status': 'out_of_domain', 'reason': 'query objects are not separated solid rectangles'}
            preds[rule] = p
        ref = preds[RULES[0]]
        disc = sorted('/'.join(r) for r in RULES if not (preds[r] == ref).all())
        if disc:
            disc = sorted(set(disc) | {'/'.join(RULES[0])})
        result['query_discriminates'].append(disc)
        first = preds[survivors[0]]
        if not all((preds[r] == first).all() for r in survivors):
            result['status'] = 'context_shortfall'
            result['query_index'] = k
            result['disagreeing_survivors'] = sorted(
                '/'.join(r) for r in survivors if not (preds[r] == first).all())
            return result
        if br is None and (first != q).any():
            result['status'] = 'colour_shortfall'
            result['query_index'] = k
            return result
    return result


def require_centred_bridge_evidence(demonstrations, queries, palette=None):
    """Raise MissingColourEvidence unless every query is identified by the demos.

    queries: [{'input': grid}, ...]; query outputs are never read. palette is
    accepted for dispatch uniformity and is only cross-checked against the
    colours inferred from the demonstrations, never used to infer them.
    """
    out = assess(demonstrations, [{'input': q['input']} for q in queries])
    if out['status'] != 'identified':
        raise MissingColourEvidence('f3b10344: ' + out['status'] + ': ' + str(
            out.get('reason', out.get('disagreeing_survivors', ''))))
    if palette is not None:
        if out['background'] != int(palette[0]) or (out['bridge'] is not None and out['bridge'] != int(palette[8])):
            raise MissingColourEvidence('f3b10344: demonstrated colours contradict the episode palette')
    return out
