def build_program(d4, palette):
    # Layout in canonical orientation: the smallest square sits at the LEFT end,
    # squares grow towards the right, and all are aligned to the BOTTOM edge.
    # A clockwise rotation maps edges L->T, T->R, R->B, B->L.
    # A row reversal (d4 >= 4, applied first) swaps L and R.
    rot = {'L': 'T', 'T': 'R', 'R': 'B', 'B': 'L'}
    start, align = 'L', 'B'
    if d4 >= 4:
        start = 'R'
    for _ in range(d4 % 4):
        start = rot[start]
        align = rot[align]
    bg = int(palette[7])
    template = '''import numpy as np

BG = __BG__
START = '__START__'
ALIGN = '__ALIGN__'

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    vals, cnts = np.unique(g, return_counts=True)
    items = []
    for v, c in zip(vals.tolist(), cnts.tolist()):
        if v == BG:
            continue
        s = int(round(float(c) ** 0.5))
        if s < 1:
            s = 1
        items.append((s, int(v)))
    if not items:
        return [[BG]]
    items.sort()
    H = max(s for s, _ in items)
    W = sum(s for s, _ in items) + len(items) - 1
    horizontal = START in ('L', 'R')
    if horizontal:
        out = np.full((H, W), BG, dtype=int)
    else:
        out = np.full((W, H), BG, dtype=int)
    x = 0
    for s, v in items:
        if START in ('L', 'T'):
            a0 = x
        else:
            a0 = W - x - s
        if ALIGN in ('B', 'R'):
            b0 = H - s
        else:
            b0 = 0
        if horizontal:
            out[b0:b0 + s, a0:a0 + s] = v
        else:
            out[a0:a0 + s, b0:b0 + s] = v
        x += s + 1
    return out.tolist()
'''
    return (template.replace('__BG__', str(bg))
                    .replace('__START__', start)
                    .replace('__ALIGN__', align))
