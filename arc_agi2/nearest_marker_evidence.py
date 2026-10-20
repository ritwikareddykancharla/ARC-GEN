"""Distance and tie conventions must be supported by visible demonstrations.

Compare three nearest-cell metrics, four secondary criteria, and eight spatial
scans. This finite hypothesis set does not establish universal identifiability.
Ambiguous scenes remain supported when their context resolves the decision.
"""
from collections import Counter
from itertools import product

from .colour_evidence import MissingColourEvidence


def marker_candidates(g, palette):
    shape = [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == palette[5]]
    markers = [(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row)
               if v not in (palette[0],palette[5])]
    if not shape or not markers:
        raise MissingColourEvidence('6df30ad6: expected a shape and markers')
    metrics = []
    for r,c,v in markers:
        offsets = [(abs(r-y),abs(c-x)) for y,x in shape]
        metrics.append((min(max(dy,dx) for dy,dx in offsets),
                        min(dy+dx for dy,dx in offsets),
                        min(dy*dy+dx*dx for dy,dx in offsets)))
    scans = list(product((True,False),(1,-1),(1,-1)))
    colours = []
    for primary in range(3):
        closest = min(m[primary] for m in metrics)
        near = [i for i,m in enumerate(metrics) if m[primary] == closest]
        counts = Counter(markers[i][2] for i in near)
        # No secondary preference, majority, Manhattan, squared Euclidean.
        for secondary in range(4):
            def rank(i):
                return (0 if secondary == 0 else -counts[markers[i][2]] if secondary == 1
                        else metrics[i][secondary-1])
            best = min(rank(i) for i in near)
            remaining = [i for i in near if rank(i) == best]
            for rows_first,rs,cs in scans:
                def scan(i):
                    r,c,_ = markers[i]
                    return (rs*r,cs*c) if rows_first else (cs*c,rs*r)
                colours.append(markers[min(remaining,key=scan)][2])
    return colours


def marker_output(g, colour, palette):
    return [[colour if v == palette[5] else palette[0] for v in row] for row in g]


def require_marker_evidence(demonstrations, queries, palette):
    possible = set(range(96))
    for demo in demonstrations:
        candidates = marker_candidates(demo['input'],palette)
        valid_colours = {v for v in set(candidates)
                         if marker_output(demo['input'],v,palette) == demo['output']}
        possible &= {i for i,v in enumerate(candidates) if v in valid_colours}
    if not demonstrations or not possible:
        raise MissingColourEvidence('6df30ad6: demonstrations fit no distance/tie convention')
    for query in queries:
        candidates = marker_candidates(query['input'],palette)
        if len({candidates[i] for i in possible}) != 1:
            raise MissingColourEvidence('6df30ad6: demonstrations leave distance/tie convention ambiguous')
