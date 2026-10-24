"""Demo-only evidence for 6d1d5c90's control-strip cyclic shift.

Finite competing rules: remove the native control strip, then shift either
picture axis by (a * marker_index + b), for 0 <= a,b < 30. Includes identity,
constant shifts, opposite direction, end-relative offsets and off-by-one rules.
This bounded hypothesis class is not a proof against every conceivable rule.
Colour/D4 metadata normalizes coordinates; query outputs are never accepted.
"""
from .augmentation import transformed


def native(g, palette, d4):
    inverse = {v: k for k, v in enumerate(palette)}
    a = [[inverse[c] for c in row] for row in g]
    a = transformed(a, (-d4) % 4, list(range(10)))
    if d4 >= 4:
        a = [row[::-1] for row in a]
    return a


def unpack(g):
    if len(g) < 2 or len(g[0]) < 2:
        raise ValueError('Control strip and nonempty picture required')
    strip = [r[0] for r in g]
    if strip.count(2) != 1 or any(c not in (2, 6) for c in strip):
        raise ValueError('Expected one marker and strip filler')
    return strip.index(2), tuple(tuple(r[1:]) for r in g)


def roll(pic, axis, shift):
    n = len(pic) if axis == 0 else len(pic[0])
    shift %= n
    if axis == 0:
        return tuple(pic[(r - shift) % n] for r in range(n))
    return tuple(tuple(row[(c - shift) % n] for c in range(n)) for row in pic)


def require_marker_roll_evidence(demonstrations, queries, palette=None, d4=0):
    from .colour_evidence import MissingColourEvidence
    palette = list(range(10)) if palette is None else palette
    alive = {(axis, a, b) for axis in (0, 1) for a in range(30) for b in range(30)}
    for pair in demonstrations:
        p, pic = unpack(native(pair['input'], palette, d4))
        expected = tuple(tuple(row) for row in native(pair['output'], palette, d4))
        matches = {}
        for axis in (0, 1):
            n = len(pic) if axis == 0 else len(pic[0])
            matches[axis] = {s for s in range(n) if roll(pic, axis, s) == expected}
        alive = {(axis, a, b) for axis, a, b in alive
                 if (a*p+b) % (len(pic) if axis == 0 else len(pic[0])) in matches[axis]}
        if not alive:
            raise MissingColourEvidence('6d1d5c90: demos fit no control-strip shift rule')
    for query in queries:
        p, pic = unpack(native(query['input'], palette, d4))
        shifts = {(axis, (a*p+b) % (len(pic) if axis == 0 else len(pic[0])))
                  for axis, a, b in alive}
        first = None
        for axis, shift in shifts:
            prediction = roll(pic, axis, shift)
            if first is None:
                first = prediction
            elif first != prediction:
                raise MissingColourEvidence('6d1d5c90: demos leave marker-to-shift relation ambiguous')
