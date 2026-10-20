def build_program(d4, palette):
    bg = int(palette[0])
    src = '''import numpy as np
from collections import Counter

BG = %d

def solve(demonstrations, grid):
    g = np.array(grid, dtype=int)
    h, w = g.shape
    s = min(h, w)
    blocks = []
    if w >= h:
        n = w // s
        for i in range(n):
            blocks.append(g[:, i * s:(i + 1) * s].copy())
    else:
        n = h // s
        for i in range(n):
            blocks.append(g[i * s:(i + 1) * s, :].copy())
    if not blocks:
        return g.tolist()
    keys = [tuple(map(tuple, (b != BG).astype(int))) for b in blocks]
    cnt = Counter(keys)
    uniques = [i for i, k in enumerate(keys) if cnt[k] == 1]
    if len(uniques) == 1:
        idx = uniques[0]
    elif uniques:
        sizes = [int(np.sum(np.array(keys[i]))) for i in uniques]
        common_key = cnt.most_common(1)[0][0]
        base = int(np.sum(np.array(common_key)))
        idx = uniques[0]
        for i, sz in zip(uniques, sizes):
            if sz != base:
                idx = i
                break
    else:
        idx = 0
    return blocks[idx].tolist()
''' % bg
    return src
