"""Batch-2 probe: native orientation of 7e2bad24/7e576d6e and blocker rate of 69889d6e.

Read-only; run from the worktree root with PYTHONPATH=. (seeded, deterministic).
"""
import random
import sys

sys.path.insert(0, '.')
from tasks import task_69889d6e as c, task_7e2bad24 as a, task_7e576d6e as b


def axis(g, cols):
    h = sum(1 for r in range(len(g)) for x in range(len(g[0]) - 1) if g[r][x] in cols and g[r][x + 1] in cols)
    v = sum(1 for r in range(len(g) - 1) for x in range(len(g[0])) if g[r][x] in cols and g[r + 1][x] in cols)
    return 'h' if h > v else 'v'


random.seed(0)
A = [a.generate() for _ in range(200)]
print('7e2bad24 wall axes', {axis(p['input'], (2, 3)) for p in A},
      'beam starts on top/left edge', all(any(p['input'][0][x] == 1 for x in range(16)) or
                                          any(p['input'][r][0] == 1 for r in range(16)) for p in A))
B = [b.generate() for _ in range(100)]
# horizontal full-width lines make every column non-uniform; transposed scenes have uniform background columns
print('7e576d6e horizontal-line scenes', sum(1 for p in B if all(len({p['input'][r][x] for r in range(30)}) > 1
                                                                  for x in range(30))), 'of', len(B))
C = [c.generate() for _ in range(2000)]
print('69889d6e mean blockers', sum(sum(v == 1 for row in p['input'] for v in row) for p in C) / len(C))
