"""Batch-3 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Usage: configured_clip_d304284e.py N [SEED]

For the approved (width, height) overrides of d304284e (audit approved_parameters),
draws N scenes per size through the real generate(width=, height=) and counts how
often the input sprite (the 7-coloured cells, drawn at brow 2..8 with tall 3..5,
task lines 35-36) is cut by the bottom edge. A sprite is "clipped" when the number
of visible input cells is smaller than the number of 1s in the sprite mask.
"""
import sys, random
sys.path.insert(0, '.')
import common
from tasks import task_d304284e as m

n = int(sys.argv[1])
random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
sizes = [(12, 10), (14, 12), (20, 14), (14, 20), (24, 21), (27, 24), (30, 27), (28, 23)]
for w, h in sizes:
    clipped = 0
    for _ in range(n):
        tall = common.randint(3, 5)
        brow, bcol = common.randint(2, 8), common.randint(2, 8)
        while True:
            rows, cols = common.conway_sprite(3, tall, common.randint(1, 8))
            if common.diagonally_connected(list(zip(rows, cols))): break
        colors = [0] * (3 * tall)
        for r, c in zip(rows, cols): colors[r * 3 + c] = 1
        g = m.generate(tall=tall, colors=colors, brow=brow, bcol=bcol, width=w, height=h)["input"]
        visible = sum(v != 0 for row in g for v in row)
        clipped += visible < sum(colors)
    print(f"width={w} height={h}: input sprite clipped by bottom edge in {clipped}/{n}")
