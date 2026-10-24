"""Batch-3 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: stuck_scenes_bb52a14b.py N_SCENES MAX_REDRAWS [SEED]

Mirrors tasks/task_bb52a14b.py lines 59-71 (pattern, box count, box centres are
drawn ONCE, outside the noise loop) and then redraws only the noise as lines
72-84 do, calling the real generate(colors=...) to test acceptance (draw()
returning None makes generate return input None). A scene that fails
MAX_REDRAWS noise redraws is "stuck"; it is then retried with zero noise
(boxes only) to see whether the boxes alone make draw() reject, i.e. whether
the native while-True loop at line 72 can never terminate for that scene.
"""
import sys, random, collections
sys.path.insert(0, '.')
import common
from tasks import task_bb52a14b as m

n, max_redraws = int(sys.argv[1]), int(sys.argv[2])
random.seed(int(sys.argv[3]) if len(sys.argv) > 3 else 0)


def scene():
    pattern = [common.choice([1, 8]) for _ in range(9)]
    if common.randint(0, 1):
        pattern[0] = pattern[2] = pattern[6] = pattern[8] = 0
        if common.randint(0, 1): pattern[4] = 0
    else:
        pattern[1] = pattern[3] = pattern[5] = pattern[7] = 0
    pattern[common.choice([0, 1, 2, 3, 5, 6, 7, 8])] = 0
    k = common.randint(2, 3)
    while True:
        rows = [common.randint(1, 20) for _ in range(k)]
        cols = [common.randint(1, 20) for _ in range(k)]
        if not common.overlaps(rows, cols, [7] * k, [7] * k): break
    return pattern, rows, cols


def colours(pattern, rows, cols, noise=True):
    g = common.grid(22, 22)
    for r in range(22):
        for c in range(22):
            g[r][c] = (0 if common.randint(0, 4) else common.choice([1, 8])) if noise else 0
    for i, (row, col) in enumerate(zip(rows, cols)):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                v = pattern[(dr + 1) * 3 + dc + 1]
                g[row + dr][col + dc] = 4 if not i and not v else v
    return common.flatten(g)


ok = stuck = stuck_det = 0
redraws = collections.Counter()
examples = []
for _ in range(n):
    p, rs, cs = scene()
    for t in range(1, max_redraws + 1):
        if m.generate(colors=colours(p, rs, cs))["input"] is not None:
            ok += 1; redraws[min(t, 10)] += 1; break
    else:
        stuck += 1
        det = m.generate(colors=colours(p, rs, cs, noise=False))["input"] is None
        stuck_det += det
        if len(examples) < 4:
            examples.append({"pattern": p, "rows": rs, "cols": cs, "boxes_alone_rejected": det})
print("scenes", n, "accepted", ok, "stuck_after", max_redraws, "redraws:", stuck,
      "of_which_rejected_with_zero_noise", stuck_det)
print("accepted redraw counts (10 = 10+):", dict(sorted(redraws.items())))
for e in examples: print("stuck example", e)
