"""Count distinct demo-set/query combinations without using output labels.

These are upper bounds before semantic evidence and program verification, not
proof that every combination is teachable. Demo permutations never add support.
"""
from collections import Counter
import math

VERSION = 'distinct-context-upper-budget-v1'


def bounds(rows, identity_key, stored_context=False):
    """Per-query-stratum upper bound with three identity-distinct demos."""
    if len({r['input_hash'] for r in rows}) != len(rows):
        raise ValueError('Query inputs must be exact-distinct')
    if stored_context:
        return dict(Counter(r['stratum'] for r in rows))
    classes = Counter(r[identity_key] for r in rows)
    # Elementary symmetric polynomials: weighted choices from distinct classes.
    e = [1, 0, 0, 0]
    for count in classes.values():
        for degree in (3, 2, 1):
            e[degree] += count*e[degree-1]
    excluding = {}
    for key, count in classes.items():
        one = e[1]-count
        two = e[2]-count*one
        excluding[key] = e[3]-count*two
    result = Counter()
    for row in rows:
        result[row['stratum']] += excluding[row[identity_key]]
    return dict(result)


def reuse_limits(requested, queries, *, finite=False, stored_context=False):
    if requested < 0 or queries < 0:
        raise ValueError('Counts cannot be negative')
    if stored_context:
        return 1, 32
    if not queries:
        return 0, 32
    # Leave headroom around balanced reuse while allowing several genuinely
    # different contexts per query. Whole-episode dedup remains authoritative.
    query = max(1 if finite else 4, 2*math.ceil(requested/queries))
    pair = max(32, 4*math.ceil(4*requested/queries))
    return query, pair
