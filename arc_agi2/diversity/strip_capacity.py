"""Enumerate feca6190 input orbits and strict same-width episode support."""
import itertools
import json
from collections import defaultdict
from pathlib import Path

from ..finite_input_policy import input_split
from .prepare import input_orbit


def colour_patterns(length):
    """One representative of each equality pattern, up to colour permutation."""
    def extend(prefix):
        if len(prefix) == length:
            yield tuple(prefix)
        else:
            for value in range(1, max(prefix, default=0) + 2):
                yield from extend(prefix + [value])
    yield from extend([])


def enumerate_domain(max_width, max_count, repeated):
    bins = defaultdict(lambda: defaultdict(dict))
    for width in range(2, max_width + 1):
        for n in range(1, min(width, max_count, 30 // width) + 1):
            patterns = list(colour_patterns(n)) if repeated else [tuple(range(1, n + 1))]
            for positions in itertools.combinations(range(width), n):
                for pattern in patterns:
                    row = [0] * width
                    for colour, col in zip(pattern, positions):
                        row[col] = colour
                    orbit = input_orbit([row])
                    bins[input_split(orbit)][width][orbit] = len(set(pattern)) < n
    report = {}
    for split, sizes in bins.items():
        eligible = 0
        for width, identities in sizes.items():
            for query, repeats in identities.items():
                if len(identities) >= 4 and (not repeats or any(
                        value and key != query for key, value in identities.items())):
                    eligible += 1
        report[split] = {
            'orbits_by_width': {str(w): len(ids) for w, ids in sorted(sizes.items())},
            'total_input_orbits': sum(map(len, sizes.values())),
            'query_orbits_with_three_distinct_same_width_demos': eligible,
        }
    return report


if __name__ == '__main__':
    report = {
        'task_id': 'feca6190',
        'method': 'Exhaustive position subsets and canonical colour equality patterns; '
                  'existing D4/palette input orbits and global split. Query requires '
                  'three distinct same-width demonstration orbits. Repeated-colour '
                  'query additionally needs another repeated-colour demonstration.',
        'domains': {
            'previous_native_plus_rearc': enumerate_domain(6, 5, False),
            'expanded_distinct_only': enumerate_domain(30, 9, False),
            'expanded_with_repeated_colours': enumerate_domain(30, 9, True),
        },
    }
    path = Path(__file__).parents[1] / 'reports/diversity-v1/feca6190-domain-capacity.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({name: {split: r['query_orbits_with_three_distinct_same_width_demos']
                            for split, r in domain.items()}
                      for name, domain in report['domains'].items()}))
