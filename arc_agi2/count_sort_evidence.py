"""Teach count-sort fill direction and first-appearance tie conventions."""
from collections import Counter
from .colour_evidence import _require_rule_agreement


def raster_paths(h,w):
    paths = []
    for rows_first in (True,False):
        for row_reverse in (False,True):
            for col_reverse in (False,True):
                rows = list(range(h))[::-1] if row_reverse else list(range(h))
                cols = list(range(w))[::-1] if col_reverse else list(range(w))
                paths.append([(r,c) for r in rows for c in cols] if rows_first
                             else [(r,c) for c in cols for r in rows])
    return paths


def count_sort_variants(g):
    h,w = len(g),len(g[0])
    counts = Counter(v for row in g for v in row)
    paths = raster_paths(h,w)
    sequences = []
    for scan in paths:
        first = {}
        for i,(r,c) in enumerate(scan): first.setdefault(g[r][c],i)
        colours = sorted(counts,key=lambda v:(-counts[v],first[v]))
        sequences.append([v for v in colours for _ in range(counts[v])])
    outputs = []
    for fill in paths:
        for sequence in sequences:
            out = [[0]*w for _ in range(h)]
            for (r,c),v in zip(fill,sequence): out[r][c] = v
            outputs.append(out)
    return outputs


def require_count_sort_evidence(demonstrations,queries):
    # All 8 fill paths x 8 tie scans; closed under D4 and palette changes.
    # No claim that this excludes every arbitrary colour-specific ordering.
    _require_rule_agreement('bd283c4a',demonstrations,queries,count_sort_variants)
