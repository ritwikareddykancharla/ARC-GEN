"""Finite demonstration-evidence check for colour-matched self-tiling (973e499e).

Compare equal/unequal/all-cell masks, outer vs inner paint colours, and
independent orientations of the block map and tile. All surviving rules must
agree on each query input. Fill is inferred from demonstration colours, never
from query answers or generator metadata. This is a bounded competitor test,
not a proof of universal rule identifiability.
"""
from itertools import product
import numpy as np
from .colour_evidence import MissingColourEvidence


def _orient(a, code):
    # Four reflections/half turns preserve rectangles; the other four require
    # square tiles. This set is closed under conjugation by episode-wide D4.
    if code >= 4:
        a = a.T
    if code & 1:
        a = a[::-1, :]
    if code & 2:
        a = a[:, ::-1]
    return a


def predict(g, spec):
    relation, outer_code, inner_code, paint, fill = spec
    a = np.asarray(g, dtype=np.int64)
    h, w = a.shape
    if h != w and (outer_code >= 4 or inner_code >= 4):
        return None
    outer = _orient(a, outer_code)[:, None, :, None]
    inner = _orient(a, inner_code)[None, :, None, :]
    selected = outer == inner if relation == 'equal' else (
        outer != inner if relation == 'unequal' else np.ones((h,h,w,w), dtype=bool))
    out = np.where(selected, outer if paint == 'outer' else inner, fill)
    return tuple(map(tuple, out.reshape(h*h, w*w).tolist()))


def surviving_rules(demonstrations):
    if not demonstrations:
        raise MissingColourEvidence('973e499e: missing demonstrations')
    fills = set(range(10))
    for demo in demonstrations:
        inside = {v for row in demo['input'] for v in row}
        extra = {v for row in demo['output'] for v in row} - inside
        if len(extra) > 1:
            return []
        if extra:
            fills &= extra
    rules = list(product(('equal','unequal','all'), range(8), range(8),
                         ('outer','inner'), sorted(fills)))
    for demo in demonstrations:
        expected = tuple(map(tuple, demo['output']))
        rules = [r for r in rules if predict(demo['input'], r) == expected]
        if not rules:
            break
    return rules


def candidate_predictions(demonstrations, query_input):
    return {predict(query_input, spec) for spec in surviving_rules(demonstrations)}


def require_self_match_evidence(demonstrations, queries):
    survivors = surviving_rules(demonstrations)
    if not survivors:
        raise MissingColourEvidence('973e499e: demonstrations fit no candidate rule')
    for query in queries:
        answers = {predict(query['input'], spec) for spec in survivors}
        if len(answers) != 1 or None in answers:
            raise MissingColourEvidence('973e499e: demonstrations leave self-match query ambiguous')
