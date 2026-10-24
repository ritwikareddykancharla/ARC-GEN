"""Enumerate query support, not episode capacity, under the current split.

RE-ARC generate_8403a5d5 samples 3..30 rows/columns, one seed in the bottom
row at columns 1..w-1, and two distinct non-grey colours. D4/palette identity
removes colour choice. Native default is size10 and also permits column0.
Strict canonical shape matching needs four distinct same-shape input orbits.
Different demo contexts could reuse a query; this exporter deliberately does not.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from .prepare import input_orbit
from ..finite_input_policy import input_split, POLICY_SIGNATURE
from ..runtime import BASE


def audit():
    support = defaultdict(set)
    domain = set()
    cases = [(h, w, c) for h in range(3, 31) for w in range(3, 31) for c in range(1, w)]
    cases += [(10, 10, c) for c in range(10)]
    for h, w, c in cases:
        grid = [[0] * w for _ in range(h)]
        grid[-1][c] = 1
        key = input_orbit(grid)
        domain.add(key)
        if input_split(key) == 'validation':
            support[h, w].add(key)
    eligible = {f'{h}x{w}': sorted(ids) for (h, w), ids in support.items() if len(ids) >= 4}
    queries = set().union(*(set(v) for v in eligible.values()))
    sources = [Path(__file__), BASE/'diversity/rearc/generators.py',
               BASE.parent/'tasks/task_8403a5d5.py', BASE/'finite_input_policy.py',
               BASE/'diversity/prepare.py']
    return dict(task_id='8403a5d5', domain_input_orbits=len(domain),
                canonical_shape_policy='uniform demo input shapes; query shape seen',
                split_signature=POLICY_SIGNATURE,
                supported_distinct_validation_query_orbits=len(queries),
                eligible_shape_bins=eligible,
                source_sha256={str(p.relative_to(BASE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                limitation='Bound on unique query identities under this split and four-orbit, same-shape context policy; NOT a bound on distinct episode contexts or future expanded generators.')


if __name__ == '__main__':
    result = audit()
    path = BASE/'reports/diversity-v1/8403a5d5-query-support.json'
    path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('eligible_shape_bins','source_sha256')}))
