def build_program(d4, palette):
    d4 = int(d4)

    def tf(vec):
        dr, dc = vec
        if d4 >= 4:
            dc = -dc
        for _ in range(d4 % 4):
            dr, dc = dc, -dr
        return (dr, dc)

    up = tf((-1, 0))
    right = tf((0, 1))
    if up == (-1, 0):
        base = 'bottom'
    elif up == (1, 0):
        base = 'top'
    elif up == (0, -1):
        base = 'right'
    else:
        base = 'left'
    if base in ('bottom', 'top'):
        step = right[1]
    else:
        step = right[0]
    bg = int(palette[0])
    push = int(palette[1])
    follow = int(palette[2])

    template = """import numpy as np
from collections import Counter

BG = %BG%
PUSH = %PUSH%
FOLLOW = %FOLLOW%
BASE = '%BASE%'
STEP = %STEP%


def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    H, W = g.shape
    out = g.copy()
    vertical = BASE in ('bottom', 'top')
    n = W if vertical else H
    if vertical:
        base_idx = H - 1 if BASE == 'bottom' else 0
    else:
        base_idx = W - 1 if BASE == 'right' else 0
    order = range(n) if STEP > 0 else range(n - 1, -1, -1)
    bars = []
    for i in order:
        if vertical:
            cells = [(r, i) for r in range(H) if g[r, i] != BG]
        else:
            cells = [(i, c) for c in range(W) if g[i, c] != BG]
        if not cells:
            continue
        colour = Counter(int(g[y, x]) for y, x in cells).most_common(1)[0][0]
        bars.append((i, cells, colour))
    prev_fell = False
    prev_next = None
    for i, cells, colour in bars:
        h = len(cells)
        falls = colour == PUSH or (prev_fell and (i - prev_next) * STEP <= 0)
        if falls:
            for y, x in cells:
                out[y, x] = BG
            for k in range(h):
                j = i + STEP * k
                if 0 <= j < n:
                    if vertical:
                        out[base_idx, j] = colour
                    else:
                        out[j, base_idx] = colour
            prev_fell = True
            prev_next = i + STEP * h
        else:
            prev_fell = False
    return out.tolist()
"""
    prog = (template.replace('%BG%', str(bg))
                    .replace('%PUSH%', str(push))
                    .replace('%FOLLOW%', str(follow))
                    .replace('%BASE%', base)
                    .replace('%STEP%', str(int(step))))
    return prog
