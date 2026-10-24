"""Batch-2 review probe, read-only. Run from the worktree root with PYTHONPATH=.

Counts native 689c358e scenes where two pluses mark the same frame row/column (2000 seeded draws).
"""
import sys, random, collections
sys.path.insert(0,'.')
import common
from tasks import task_689c358e as m
random.seed(0)
N=2000; conflict=0; nat=0
for _ in range(N):
    while True:
        rows, cols, angles = [], [], []
        for _ in range(4):
            angle, lb_row, lb_col, ub_row, ub_col = common.randint(0, 3), 2, 2, 8, 8
            if angle == 0: lb_row, ub_row = 4, 7
            if angle == 1: lb_col, ub_col = 3, 6
            if angle == 2: lb_row, ub_row = 3, 6
            if angle == 3: lb_col, ub_col = 4, 7
            angles.append(angle); rows.append(common.randint(lb_row, ub_row)); cols.append(common.randint(lb_col, ub_col))
        g = m.generate(rows=rows, cols=cols, angles=angles)
        if g['input']: break
    keys=[('c',c) if a in (0,2) else ('r',r) for r,c,a in zip(rows,cols,angles)]
    if len(set(keys))<4: conflict+=1
print('border-line conflicts', conflict, 'of', N)
