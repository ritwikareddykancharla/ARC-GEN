"""Batch-2 review probe (corrected 2026-10-24), read-only. Run from the worktree root with PYTHONPATH=.

Part 1 is the canonical counterexample. Canonical train[2] (also native validate()['train'][2])
has a red line that exits through the bottom edge at column 8. Column 9 therefore contains no
red (2), and the output's column 9 is all zeros. Bottom exits and the cleared red-free column
are fixture-supported behaviour, not invalid scenes.

Part 2 is the finite sample statistic: 3000 native draws, seed 0. It counts inputs with at
least one red-free column. For each such column it checks that the output is all zeros, as in
the canonical pair. It also compares the factory's top-edge flood with the native outputs.
"""
import sys, random
sys.path.insert(0, '.')
from arc_agi2 import runtime
from tasks import task_782b5218 as m
import importlib.util


def red_free_cols(grid):
    return [c for c in range(len(grid[0])) if all(grid[r][c] != 2 for r in range(len(grid)))]


# Part 1: canonical counterexample.
can = runtime.reference('782b5218')['canonical']
val = m.validate()
for name, pair in (('canonical train[2]', can['train'][2]), ('validate() train[2]', val['train'][2])):
    cols = red_free_cols(pair['input'])
    blank = all(pair['output'][r][c] == 0 for c in cols for r in range(10))
    print(f"{name}: red-free columns {cols}; output all-zero in those columns: {blank}")
print('canonical train[2] == validate() train[2]:', can['train'][2] == val['train'][2])

# Part 2: finite native sample (unchanged seed and N, so the count matches the batch-2 review).
spec = importlib.util.spec_from_file_location('f', 'arc_agi2/direct_factories/task_782b5218.py')
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
ns = {}; exec(f.build_program(0, list(range(10))), ns)
random.seed(0); N = 3000; miss = 0; blank_ok = 0; dis = 0; ex = 0
for _ in range(N):
    p = m.generate(); g = p['input']
    cols = red_free_cols(g)
    if cols:
        miss += 1
        blank_ok += all(p['output'][r][c] == 0 for c in cols for r in range(10))
    try:
        o = ns['_apply'](g, 'top').tolist()
        if o != p['output']: dis += 1
    except Exception: ex += 1
print('cols_without_red', miss, 'of_which_output_blank_in_those_cols', blank_ok,
      'factory_top_disagree', dis, 'exceptions', ex, 'of', N)
